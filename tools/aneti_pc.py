# -*- coding: utf-8 -*-
"""Relevé de l'ANETI (emploi.nat.tn) DEPUIS LE PC d'Ahmed -> donnees/aneti/, puis envoi sur GitHub.

Pourquoi en local (règle d'Ahmed du 08/10/2026) : le site de l'ANETI ne répond qu'aux connexions venant de Tunisie
(il coupe celles de GitHub et du cloud : « connection reset »). Ce n'est pas un contournement : c'est une visite normale
depuis la Tunisie, une fois par jour, lente (2 s entre deux pages), en se présentant ; robots.txt de l'ANETI : tout autorisé.

Le PC ne fait QUE télécharger (aucun tri) : la liste des pages est dans tools/aneti_a_lire.json (modifiable depuis
GitHub, relue à chaque passage) ; les pages brutes vont dans donnees/aneti/ ; c'est le robot de GitHub qui les lit
ensuite (concours pour ce site, nouveaux documents pour le site Documents). Ainsi tout se corrige sans toucher au PC.

Lancé chaque jour à 12h30 par la tâche planifiée Windows « Concours-ANETI » (tools/installer_aneti_pc.ps1) ;
si le PC est éteint à 12h30 : dès qu'il est rallumé. Sans le PC, les sites continuent (seul l'ANETI manque).

Usage : python tools/aneti_pc.py           Journal : tools/aneti_pc.log (non envoyé)
        python tools/aneti_pc.py --essai   (télécharge sans rien envoyer)
"""
import datetime
import json
import re
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONF = ROOT / "tools" / "aneti_a_lire.json"
SORTIE = ROOT / "donnees" / "aneti"
LOG = ROOT / "tools" / "aneti_pc.log"
AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36 "
         "alerte-concours-tunisie (site gratuit d'information ; une lecture par jour)")
PAUSE = 2.0
MAX_TOTAL = 80          # jamais plus de 80 pages par jour


def log(msg):
    ligne = f"{datetime.datetime.now():%Y-%m-%d %H:%M} {msg}"
    print(ligne)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(ligne + "\n")


def git(*args):
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)} : {r.stderr.strip()}")
    return r.stdout


def telecharger(url):
    req = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept-Language": "fr,ar;q=0.8"})
    try:
        r = urllib.request.urlopen(req, timeout=60)
    except urllib.error.URLError as e:
        # plusieurs sites de l'État ont un certificat incomplet (même cas que Géant : « curl -k ») ; page publique, lecture seule
        if "CERTIFICATE_VERIFY_FAILED" not in str(e):
            raise
        r = urllib.request.urlopen(req, timeout=60, context=ssl._create_unverified_context())
    with r:
        brut = r.read()
        enc = r.headers.get_content_charset() or "utf-8"
    return r.status, brut.decode(enc, "replace")


def nom_fichier(t):
    return re.sub(r"[^a-z0-9-]+", "-", t.lower()).strip("-")[:80] or "page"


def relever(conf):
    """Télécharge les pages de la liste (et leurs liens « suivre ») ; renvoie le résumé du relevé."""
    SORTIE.mkdir(parents=True, exist_ok=True)
    for vieux in SORTIE.glob("*.html"):          # on ne garde que le relevé du jour
        vieux.unlink()
    resume, total = {"date": datetime.date.today().isoformat(), "heure": f"{datetime.datetime.now():%H:%M}", "pages": []}, 0
    for p in conf.get("pages", []):
        a_faire = [(p["nom"], p["url"])]
        while a_faire and total < MAX_TOTAL:
            nom, url = a_faire.pop(0)
            total += 1
            try:
                code, texte = telecharger(url)
                (SORTIE / f"{nom_fichier(nom)}.html").write_text(texte, encoding="utf-8")
                resume["pages"].append({"nom": nom_fichier(nom), "url": url, "code": code, "taille": len(texte)})
                if p.get("suivre") and nom == p["nom"]:
                    liens = []
                    for l in re.findall(p["suivre"], texte):
                        l = urllib.parse.urljoin(url, l.replace("&amp;", "&"))
                        if l not in liens:
                            liens.append(l)
                    for l in liens[: int(p.get("max", 20))]:
                        ref = re.search(r"ref=(\d+)", l)
                        a_faire.append((f"{p['nom']}-detail-{ref.group(1) if ref else len(a_faire)}", l))
            except Exception as e:
                resume["pages"].append({"nom": nom_fichier(nom), "url": url, "erreur": str(e)[:200]})
            time.sleep(PAUSE)
    (SORTIE / "releve.json").write_text(json.dumps(resume, ensure_ascii=False, indent=1), encoding="utf-8")
    return resume


def main():
    essai = "--essai" in sys.argv
    try:
        if not essai:
            git("pull", "--rebase", "--autostash", "origin", "main")
        conf = json.loads(CONF.read_text(encoding="utf-8"))
        r = relever(conf)
        ok = [x for x in r["pages"] if "erreur" not in x]
        log(f"{len(ok)} page(s) téléchargée(s) sur {len(r['pages'])}" + ("" if len(ok) == len(r["pages"]) else
            " — échecs : " + ", ".join(x["nom"] for x in r["pages"] if "erreur" in x)))
        if essai or not ok:
            return 0 if ok else 1
        git("add", "-A", "--", "donnees/aneti")
        if subprocess.run(["git", "-C", str(ROOT), "diff", "--cached", "--quiet"]).returncode == 0:
            log("rien de nouveau")
            return 0
        git("commit", "-m", f"Relevé ANETI depuis le PC ({r['date']})", "--", "donnees/aneti")
        git("push", "origin", "main")
        log("envoyé sur GitHub")
    except Exception as e:
        log(f"ÉCHEC : {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
