"""Robot d'Alerte Concours Tunisie : lit les ACTUALITÉS du portail des concours publics (www.concours.gov.tn) :
nouveaux concours annoncés, listes des candidatures acceptées, convocations, résultats, reports… et écrit
donnees/actualites.json.

  python robot/lire_actualites.py                  (nouvelles actualités seulement, 2 s entre deux pages)
  python robot/lire_actualites.py --fichier X.html (sans réseau : lit une actualité enregistrée, pour les tests)

Liste : page « الأخبار » (P1/index15.aspx?id=pub) ; chaque actualité : P1/index31.aspx?id=<n> (organisme, date, texte).
Données : faits publics + RÉSUMÉ court (300 caractères au plus) + lien officiel ; jamais le texte entier.
Chaque actualité est rattachée, si possible, aux concours du même organisme (donnees/concours.json) : c'est la base
du futur « Suivi de mes concours ». Panne du portail : l'ancien fichier est gardé, le site reste en ligne (sortie 0,
avec un message « ÉCHEC » dans le journal ; les concours, eux, sont lus par lire_concours.py)."""
import argparse, datetime as dt, html, json, os, re, sys, time, urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
SORTIE = os.path.join(RACINE, "donnees", "actualites.json")
CONCOURS = os.path.join(RACINE, "donnees", "concours.json")
LISTE = "https://www.concours.gov.tn/P1/index15.aspx?id=pub"
DETAIL = "https://www.concours.gov.tn/P1/index31.aspx?id={}"
AGENT = "alerte-concours-tunisie/1.0 (site gratuit d'information ; robot lent, 1 page toutes les 2 s)"
PAUSE = 2.0
BUDGET = 300          # secondes au plus pour lire les actualités (portail qui ne répond plus, 08/10/2026 : bloqué 20 min)
ECHECS_DE_SUITE = 3   # 3 actualités illisibles de suite : le portail est en panne, on s'arrête (reprise demain)
PREMIERE_FOIS = 40     # 1re lecture : les 40 dernières actualités seulement
GARDER = 300           # au plus 300 actualités gardées (les plus récentes)
RESUME = 300           # caractères au plus (jamais le texte entier)

# type d'actualité : (slug, FR, AR, mots). L'ordre compte : le premier qui correspond gagne.
TYPES = [
    ("resultats", "Résultats", "النتائج", r"نتائج|الناجحين|الناجحات|المقبولين نهائيا|القائمة النهائية|القائمات النهائية|القائمة الأولية|القائمات الأولية|قائمة الانتظار"),
    ("report", "Report ou changement", "تأجيل أو تغيير", r"تأجيل|إرجاء|تمديد|تغيير موعد|تعديل|إلغاء"),
    ("convocation", "Convocation", "استدعاء", r"استدعاء|دعوة المترشحين|مدعو|موعد الاختبار|موعد إجراء|إجراء الاختبار|سيتم إجراء"),
    ("candidatures", "Candidatures acceptées", "قبول الترشحات", r"المقبول|قبول ترشح|الترشحات المقبولة|المترشحين الذين تم قبول"),
    ("nouveau", "Nouveau concours", "مناظرة جديدة", r"يعتزم|فتح مناظرة|فتح باب|تنظيم مناظرة|مناظرة خارجية|مناظرة داخلية|انتداب"),
]
AUTRE = ("autre", "Information", "إعلام")
ARABE_EN_LATIN = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def nettoyer(t):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t or ""))).strip()


def type_de(texte):
    t = re.sub(r"[\u064B-\u0652\u0640]", "", texte or "")     # sans voyelles ni chadda ni tatouil : « النهائيّة » = « النهائية »
    for slug, _, _, motif in TYPES:
        if re.search(motif, t):
            return slug
    return AUTRE[0]


def resume(texte):
    if len(texte) <= RESUME:
        return texte
    coupe = texte[:RESUME]
    return coupe[:coupe.rfind(" ")].rstrip("،,.:؛ ") + "…" if " " in coupe else coupe + "…"


def lire_detail(page, ident):
    """Une actualité : organisme (titre), date, résumé, type. None si la page n'en est pas une."""
    m = re.search(r'<div id="Content">\s*<h2>(.*?)</h2>', page, re.S)
    a = re.search(r'<div class="Article">.*?<p[^>]*>(.*?)<a href="\.\./P1/index15\.aspx', page, re.S)
    if not m or not a:
        return None
    organisme = nettoyer(m.group(1))[:200]
    corps = nettoyer(a.group(1))
    d = re.match(r"(\d{4}-\d{2}-\d{2})\s*(.*)$", corps.translate(ARABE_EN_LATIN), re.S)
    date, texte = (d.group(1), d.group(2).strip()) if d else ("", corps)
    if not organisme or not texte:
        return None
    return {"id": str(ident), "organisme": organisme, "date": date, "type": type_de(texte), "resume": resume(texte),
            "lien": DETAIL.format(ident)}


def normal(t):
    t = re.sub("[\u064B-\u0652\u0640]", "", t or "")      # sans voyelles, chadda ni tatouil
    return re.sub(r"\s+", " ", t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي")).strip()


def rattacher(actus, concours):
    """Numéros des concours du même organisme (nom identique, à l'orthographe près)."""
    par_org = {}
    for c in concours:
        par_org.setdefault(normal(c["organisme"]), []).append(c["id"])
    for a in actus:
        a["concours"] = sorted(set(par_org.get(normal(a["organisme"]), [])), key=lambda x: int(x) if x.isdigit() else 0)
    return actus


def get(url):
    for essai in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": AGENT}), timeout=30) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception:
            if essai == 2:
                raise
            time.sleep(10 * (essai + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fichier", help="actualité HTML enregistrée (tests, sans réseau)")
    ap.add_argument("--sortie", default=SORTIE)
    ap.add_argument("--aujourdhui", default=dt.date.today().isoformat())
    a = ap.parse_args()
    ancien = json.load(open(a.sortie, encoding="utf-8")) if os.path.exists(a.sortie) else {"actualites": []}
    connus = {x["id"]: x for x in ancien["actualites"]}
    if a.fichier:
        x = lire_detail(open(a.fichier, encoding="utf-8").read(), "0")
        nouvelles = [x] if x else []
    else:
        try:
            ids = sorted({int(n) for n in re.findall(r"index31\.aspx\?id=(\d+)", get(LISTE))}, reverse=True)
        except Exception as e:
            print(f"ÉCHEC : liste des actualités illisible ({e}) ; ancien fichier gardé.")
            return
        a_lire = [i for i in ids if str(i) not in connus][: (PREMIERE_FOIS if not connus else 60)]
        nouvelles, debut, de_suite = [], time.monotonic(), 0
        for i in a_lire:
            if time.monotonic() - debut > BUDGET or de_suite >= ECHECS_DE_SUITE:
                print(f"  arrêt : portail trop lent ou en panne ; les autres actualités seront lues demain")
                break
            time.sleep(PAUSE)
            try:
                x = lire_detail(get(DETAIL.format(i)), i); de_suite = 0
            except Exception as e:
                de_suite += 1
                print(f"  actualité {i} illisible ({e})"); continue
            if x:
                x["vu_le"] = a.aujourdhui if connus else ""
                nouvelles.append(x)
        if a_lire and not nouvelles:
            print(f"ÉCHEC : {len(a_lire)} actualités à lire, aucune comprise (page du portail changée ?) ; ancien fichier gardé.")
            return
    concours = json.load(open(CONCOURS, encoding="utf-8"))["concours"] if os.path.exists(CONCOURS) else []
    toutes = list({x["id"]: x for x in ancien["actualites"] + nouvelles}.values())
    for x in toutes:
        x["type"] = type_de(x["resume"])      # règles améliorées : appliquées aussi aux anciennes actualités
    toutes.sort(key=lambda x: (x.get("date") or "", int(x["id"]) if x["id"].isdigit() else 0), reverse=True)
    donnees = {"source": LISTE, "lu_le": a.aujourdhui, "actualites": rattacher(toutes[:GARDER], concours)}
    os.makedirs(os.path.dirname(a.sortie), exist_ok=True)
    json.dump(donnees, open(a.sortie, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    par_type = {}
    for x in nouvelles: par_type[x["type"]] = par_type.get(x["type"], 0) + 1
    print(f"{len(nouvelles)} nouvelle(s) actualité(s) ; {len(donnees['actualites'])} gardées ; par type : {par_type}")


if __name__ == "__main__":
    main()
