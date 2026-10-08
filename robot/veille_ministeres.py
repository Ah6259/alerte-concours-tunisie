"""Veille hebdomadaire des sites des ministères (demande d'Ahmed du 08/10/2026) : repère les annonces de concours
publiées sur le site de chaque ministère (liste : tools/ministeres.json) -> donnees/ministeres.json.

Méthode (la même pour tous les sites, sans réglage par site) : la page d'accueil est lue ; un lien dont le texte parle de
concours (« مناظرة », « انتداب », « concours », « recrutement ») et assez long pour être un titre est une ANNONCE ;
un lien court du même genre (« المناظرات », « Concours ») est une RUBRIQUE : elle est lue aussi (3 au plus par site).
Faits publics + lien officiel, jamais le texte entier. Robot lent (2 s entre deux pages), qui se présente.
1re vérification d'un site : ses annonces sont notées sans être « nouvelles » ; ensuite, seules les nouvelles le sont.
Site injoignable : noté dans « sites » (statut, erreur) et ses anciennes annonces sont gardées ; jamais bloquant.

  python robot/veille_ministeres.py                       (tous les sites)
  python robot/veille_ministeres.py --seulement sante     (un site)
  python robot/veille_ministeres.py --fichier X.html --seulement sante   (sans réseau, tests)"""
import argparse, datetime as dt, html, json, os, re, ssl, sys, time, urllib.error, urllib.parse, urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
LISTE = os.path.join(RACINE, "tools", "ministeres.json")
SORTIE = os.path.join(RACINE, "donnees", "ministeres.json")
AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36 "
         "alerte-concours-tunisie (site gratuit d'information ; une visite par semaine)")
PAUSE = 2.0
GARDER = 400
MOTS = re.compile(r"مناظر|انتداب|إنتداب|concours|recrutement|recrute", re.I)
EXCLUS = re.compile(r"مناظرة\s+وطنية\s+للإبداع|concours\s+(?:de\s+)?(?:photo|dessin|cuisine|beaut|artistique)|r[èe]glement\s+du\s+concours|"
                    r"concours\s+\d{4}\s+«|جائزة|résultats?\s+du\s+bac|مسابقة", re.I)
# documents officiels (formulaires, imprimés, demandes) : pour le site Documents (idée d'Ahmed du 08/10/2026)
DOC_MOTS = re.compile(r"مطبوع|استمار|أنموذج|نموذج(?!ي)|نماذج|مطلب|مطالب|وثائق إدارية|الخدمات الإدارية|formulaire|imprim[ée]|mod[èe]le|"
                      r"demande d['’]|attestation|documents? administratifs?|services? administratifs?|e-services", re.I)
FICHIER_DOC = re.compile(r"\.(?:pdf|docx?|odt|xlsx?)(?:$|\?)", re.I)
TITRE_MIN = 25          # caractères : en dessous, c'est le nom d'une rubrique
MAX_RUBRIQUES = 3
ANTI_ROBOT = re.compile(r"just a moment|cf-chl|captcha|are you human|verify you are|Accès refusé|Access denied", re.I)


def nettoyer(t):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t or ""))).strip()


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept-Language": "ar,fr;q=0.8"})
    try:
        r = urllib.request.urlopen(req, timeout=30)
    except urllib.error.URLError as e:
        # plusieurs sites de l'État ont un certificat incomplet : page publique, lecture seule (comme « curl -k » pour Géant)
        if "CERTIFICATE_VERIFY_FAILED" not in str(e):
            raise
        r = urllib.request.urlopen(req, timeout=30, context=ssl._create_unverified_context())
    with r:
        brut = r.read(3_000_000)
        enc = r.headers.get_content_charset() or "utf-8"
        return r.geturl(), brut.decode(enc, "replace")


def liens(page, base):
    """(adresse complète, texte) de chaque lien de la page, sans doublon d'adresse."""
    out, vus = [], set()
    for href, texte in re.findall(r'<a\b[^>]*?href\s*=\s*["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', page, re.S | re.I):
        t = nettoyer(texte)[:300]
        if not t or href.lower().startswith(("javascript:", "mailto:", "tel:")):
            continue
        u = urllib.parse.urljoin(base, html.unescape(href.strip()))
        if u not in vus:
            vus.add(u)
            out.append((u, t))
    return out


def trier(ls):
    """Sépare les annonces (titres) et les rubriques (liens courts) qui parlent de concours."""
    annonces, rubriques = [], []
    for u, t in ls:
        if not MOTS.search(t + " " + urllib.parse.unquote(u)) or EXCLUS.search(t):
            continue
        if len(t) >= TITRE_MIN and MOTS.search(t):
            annonces.append((u, t))
        elif len(t) < TITRE_MIN:
            rubriques.append((u, t))
    return annonces, rubriques


def trier_docs(ls):
    """Documents officiels (formulaires…) et rubriques de documents d'une page."""
    docs, rubriques = [], []
    for u, t in ls:
        if not DOC_MOTS.search(t) or MOTS.search(t):
            continue
        if FICHIER_DOC.search(u) or len(t) >= TITRE_MIN:
            docs.append((u, t))
        else:
            rubriques.append((u, t))
    return docs, rubriques


def veiller_docs(site, page, base, lire=get):
    """Formulaires et documents officiels d'un site (page d'accueil déjà lue + 3 rubriques de documents au plus)."""
    docs, rubriques = trier_docs(liens(page, base))
    hote = urllib.parse.urlparse(base).netloc
    for u, _ in [r for r in rubriques if urllib.parse.urlparse(r[0]).netloc == hote][:MAX_RUBRIQUES]:
        time.sleep(PAUSE)
        try:
            b2, p2 = lire(u)
            docs += trier_docs(liens(p2, b2))[0]
        except Exception:
            pass
    vus, res = set(), []
    for u, t in docs:
        if u not in vus:
            vus.add(u)
            res.append((u, t))
    return res


def veiller(site, lire=get, avec_docs=None):
    """Annonces de concours d'un site : (statut, [(lien, titre)], erreur). avec_docs = liste où ajouter les documents trouvés."""
    try:
        base, page = lire(site["url"])
    except Exception as e:
        return "injoignable", [], str(e)[:160]
    if ANTI_ROBOT.search(page[:20000]) and len(liens(page, base)) < 15:
        return "bloque", [], "protection anti-robot (pas de contournement)"
    annonces, rubriques = trier(liens(page, base))
    if avec_docs is not None:
        avec_docs += veiller_docs(site, page, base, lire)
    hote = urllib.parse.urlparse(base).netloc
    for u, _ in [r for r in rubriques if urllib.parse.urlparse(r[0]).netloc == hote][:MAX_RUBRIQUES]:
        time.sleep(PAUSE)
        try:
            b2, p2 = lire(u)
            annonces += trier(liens(p2, b2))[0]
        except Exception:
            pass
    vus, res = set(), []
    for u, t in annonces:
        if u not in vus:
            vus.add(u)
            res.append((u, t))
    return "ok", res, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seulement")
    ap.add_argument("--fichier")
    ap.add_argument("--sortie", default=SORTIE)
    ap.add_argument("--aujourdhui", default=dt.date.today().isoformat())
    a = ap.parse_args()
    sites = [s for s in json.load(open(LISTE, encoding="utf-8"))["sites"] if s.get("actif", True) and (not a.seulement or s["id"] == a.seulement)]
    ancien = json.load(open(a.sortie, encoding="utf-8")) if os.path.exists(a.sortie) else {"sites": {}, "annonces": []}
    connues = {x["lien"]: x for x in ancien["annonces"]}
    docs_connus = {x["lien"]: x for x in ancien.get("documents", [])}
    etat, nouvelles = dict(ancien.get("sites", {})), []
    lire = (lambda url: (url, open(a.fichier, encoding="utf-8").read())) if a.fichier else get
    for s in sites:
        docs = []
        statut, annonces, err = veiller(s, lire, docs)
        for u, t in docs:
            if u in docs_connus:
                docs_connus[u]["revu_le"] = a.aujourdhui
            else:
                docs_connus[u] = {"ministere": s["id"], "titre": t, "lien": u, "vu_le": a.aujourdhui, "revu_le": a.aujourdhui}
        premiere = not any(x["ministere"] == s["id"] for x in ancien["annonces"]) and not etat.get(s["id"], {}).get("ok_le")
        etat[s["id"]] = {"statut": statut, "nb": len(annonces), "erreur": err, "vu_le": a.aujourdhui,
                         "ok_le": a.aujourdhui if statut == "ok" else etat.get(s["id"], {}).get("ok_le", "")}
        for u, t in annonces:
            if u in connues:
                connues[u]["revu_le"] = a.aujourdhui
                continue
            x = {"ministere": s["id"], "titre": t, "lien": u, "vu_le": "" if premiere else a.aujourdhui, "revu_le": a.aujourdhui}
            connues[u] = x
            nouvelles.append(x)
        print(f"{s['id']:24} {statut:12} {len(annonces):3} annonce(s) {len(docs):3} document(s) {err}")
        time.sleep(0 if a.fichier else PAUSE)
    toutes = sorted(connues.values(), key=lambda x: (x.get("vu_le") or "", x.get("revu_le") or ""), reverse=True)[:GARDER]
    os.makedirs(os.path.dirname(a.sortie), exist_ok=True)
    documents = sorted(docs_connus.values(), key=lambda x: (x.get("vu_le") or "", x["ministere"]), reverse=True)[:GARDER]
    json.dump({"lu_le": a.aujourdhui, "sites": etat, "annonces": toutes, "documents": documents}, open(a.sortie, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ok = sum(1 for v in etat.values() if v["statut"] == "ok")
    print(f"{ok}/{len(etat)} site(s) lus ; {len(nouvelles)} annonce(s) ajoutée(s) ; {len(toutes)} gardées")


if __name__ == "__main__":
    main()
