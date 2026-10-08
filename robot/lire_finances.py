"""Deuxième source officielle (accord d'Ahmed du 08/10/2026, « fais 1 ») : la plateforme des concours du ministère
des Finances, https://concours.finances.gov.tn/ (lisible depuis GitHub, testé le 08/10/2026).

Chaque annonce « تعتزم وزارة المالية فتح مناظرة … » est un tableau : grade, spécialités, nombre de postes, avis (PDF),
date d'ouverture et date de clôture des candidatures. Les blocs de résultats (« القائمة النهائية … ») sont ignorés.
Chaque ligne devient un concours au même format que ceux du portail (donnees/concours.json), classé « national »
(ministère : ouvert à toute la Tunisie), avec un numéro stable dans la plage 900000+ (jamais utilisée par le portail) :
900000 + 100 × numéro de l'annonce sur la plateforme + rang de la ligne.

  python robot/lire_finances.py                     (affiche ce qui est lu)
  python robot/lire_finances.py --fichier X.html    (sans réseau)
Utilisé par lire_concours.py ; une panne de cette source ne bloque jamais le site."""
import argparse, hashlib, html, json, re, sys, urllib.request

URL = "https://concours.finances.gov.tn/"
ORGANISME = "وزارة المالية"
AGENT = "alerte-concours-tunisie/1.0 (site gratuit d'information ; une lecture par jour)"
BLOC = re.compile(r'<div class="card card-body printableArea[^"]*"[^>]*>(.*?)</table>', re.S)


def nettoyer(t):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t or ""))).strip()


def date_iso(t):
    m = re.search(r"(\d{4})/(\d{2})/(\d{2})", t or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def lignes(page, metier=None):
    """Les concours annoncés sur la page de la plateforme (liste de dicts au format de donnees/concours.json)."""
    metier = metier or (lambda g: "autre")
    out, vus = [], set()
    for bloc in BLOC.findall(page):
        titre = nettoyer((re.search(r"<h5[^>]*>(.*?)</h5>", bloc, re.S) or [None, ""])[1])
        if not re.search(r"فتح\s+مناظرة|تعتزم", titre):
            continue                                    # résultats, listes d'admis, convocations : pas un concours ouvert
        nature = "مناظرة داخلية" if "داخلية" in titre else "مناظرة خارجية"
        for rang, tr in enumerate(re.findall(r"<tr>\s*(<td.*?)</tr>", bloc, re.S)):
            td = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
            if len(td) < 6:
                continue
            grade = nettoyer(td[0])
            specs = [nettoyer(x) for x in re.findall(r"<li[^>]*>(.*?)</li>", td[1], re.S) if nettoyer(x)]
            nb = re.sub(r"\D", "", nettoyer(td[2]))
            avis = re.search(r'href="(/theme/documents/concours/(\d+)/avis-concours\.pdf)"', td[3])
            if not grade:
                continue
            if avis:
                num = 900000 + 100 * int(avis.group(2)) + rang
            else:                                       # sans avis : numéro tiré du texte (stable d'un jour à l'autre)
                num = 990000 + int(hashlib.sha1((titre + grade).encode()).hexdigest(), 16) % 10000
            if num in vus:
                continue
            vus.add(num)
            plein = grade + (" — " + "، ".join(specs) if specs else "")
            out.append({
                "id": str(num), "decision": f"{nature} — {ORGANISME}", "organisme": ORGANISME, "grade": plein[:200],
                "postes": int(nb) if nb else None,
                "ouverture_candidatures": date_iso(nettoyer(td[4])), "cloture_candidatures": date_iso(nettoyer(td[5])),
                "cloture_concours": "", "resultat_initial": "", "resultat_final": "",
                "metier": metier(grade), "gouvernorat": "national",
                "source": "finances", "lien": URL + avis.group(1)[1:] if avis else URL,
            })
    return out


def lire(metier=None):
    req = urllib.request.Request(URL, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return lignes(r.read().decode("utf-8", "ignore"), metier)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fichier")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    import lire_concours as R
    cs = lignes(open(a.fichier, encoding="utf-8").read(), R.metier) if a.fichier else lire(R.metier)
    print(json.dumps(cs, ensure_ascii=False, indent=1))
