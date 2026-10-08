"""Robot d'Alerte Concours Tunisie : lit le tableau officiel des concours ouverts du portail des concours publics
(www.concours.gov.tn, page P1/index5.aspx?id=5), page après page, et écrit donnees/concours.json.

  python robot/lire_concours.py                 (lecture complète, 2 s entre deux pages)
  python robot/lire_concours.py --max-pages 3   (essai)
  python robot/lire_concours.py --fichier X.html (sans réseau : lit une page enregistrée, pour les tests)

Données : faits publics (organisme, grade, nombre de postes, dates, état des résultats) + lien vers le portail
officiel ; jamais le texte entier. Le portail n'a pas de robots.txt ; le robot reste lent et s'identifie.
Prudence : si la lecture ramène beaucoup moins de lignes que la fois précédente (panne du portail), l'ancien fichier
est gardé et le robot sort en erreur (GitHub prévient ; le site garde ses données).
L'historique des résultats (« لم تنشر » = pas encore publié → publié) sert au « Suivi de mes concours ».
Deuxième source (08/10/2026) : plateforme du ministère des Finances (robot/lire_finances.py), numéros 900000+,
classés « national » ; une panne de cette source garde ses concours de la veille et ne bloque jamais le site."""
import argparse, datetime as dt, html, http.cookiejar, json, os, re, sys, time, urllib.parse, urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import gouvernorats as G   # noqa: E402
import lire_finances as F  # noqa: E402
RACINE = os.path.dirname(ICI)
SORTIE = os.path.join(RACINE, "donnees", "concours.json")
URL = "https://www.concours.gov.tn/P1/index5.aspx?id=5"
AGENT = "alerte-concours-tunisie/1.0 (site gratuit d'information ; robot lent, 1 page toutes les 2 s)"
PAUSE = 2.0
MAX_PAGES = 200
JOURS_FERMES_FINANCES = 60  # concours des Finances clos depuis plus longtemps : pas repris
SEUIL_CHUTE = 0.5          # moins de 50 % des lignes de la fois précédente : lecture suspecte

# métiers : (slug, nom FR, nom AR, mots du grade). L'ordre compte : le premier qui correspond gagne.
METIERS = [
    ("ingenieur", "Ingénieurs", "المهندسون", r"مهندس"),
    ("sante", "Santé", "الصحة", r"طبيب|ممرض|شبه طبي|صيدل|قابلة|تقني سام في الصحة|إسعاف"),
    ("enseignant", "Enseignement", "التعليم", r"أستاذ|استاذ|معلم|مدرس|منشط|مرب"),
    ("informatique", "Informatique", "الإعلامية", r"إعلامي|اعلامي|مبرمج|محلل|برمجي"),
    ("finance", "Finances et contrôle", "المالية والمراقبة", r"محاسب|مالي|مراقب|متفقد|جباي|قابض"),
    ("securite", "Sécurité", "الأمن", r"أمن|حرس|ديوان[ةه]|شرط|حماية مدنية"),
    ("chauffeur", "Chauffeurs", "السواق", r"سائق|سياقة"),
    ("technicien", "Techniciens", "التقنيون", r"تقني|فني"),
    ("administratif", "Administration", "الإدارة", r"متصرف|ملحق|كاتب|مستكتب|إطار|مستشار|عون تسيير|عون إدارة"),
    ("ouvrier", "Ouvriers et agents", "العملة والأعوان", r"عامل|عملة|عون|حارس|بناء|دهان|سباك|ميكانيكي|كهربائي|نجار|منظف"),
]
AUTRE = ("autre", "Autres", "أخرى")
ARABE_EN_LATIN = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def metier(grade):
    for slug, fr, ar, motif in METIERS:
        if re.search(motif, grade or ""):
            return slug
    return AUTRE[0]


def nettoyer(t):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t or ""))).strip()


def date_iso(t):
    t = (t or "").translate(ARABE_EN_LATIN).strip()
    return t if re.fullmatch(r"\d{4}-\d{2}-\d{2}", t) else ""


def lignes(page):
    """Les lignes de concours d'une page du tableau officiel."""
    out = []
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S):
        c = [nettoyer(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
        if len(c) >= 7 and c[0].translate(ARABE_EN_LATIN).isdigit():
            num = c[0].translate(ARABE_EN_LATIN)
            nb = re.sub(r"\D", "", c[4].translate(ARABE_EN_LATIN))
            out.append({
                "id": num, "decision": c[1][:300], "organisme": c[2][:200], "grade": c[3][:200],
                "postes": int(nb) if nb else None, "cloture_candidatures": date_iso(c[5]), "cloture_concours": date_iso(c[6]),
                "resultat_initial": c[8] if len(c) > 8 else "", "resultat_final": c[9] if len(c) > 9 else "",
                "metier": metier(c[3]),
                "gouvernorat": G.gouvernorat(c[2]),
            })
    return out


def champs_caches(page):
    return {n: html.unescape(v) for n, v in re.findall(r'<input type="hidden" name="([^"]+)" id="[^"]*" value="([^"]*)"', page)}


def lire_portail(max_pages):
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def get(data=None):
        req = urllib.request.Request(URL, data=data, headers={"User-Agent": AGENT})
        for essai in range(3):
            try:
                with op.open(req, timeout=60) as r:
                    return r.read().decode("utf-8", "ignore")
            except Exception:
                if essai == 2: raise
                time.sleep(10 * (essai + 1))
    page = get(); vus = {}; n = 1
    for l in lignes(page): vus[l["id"]] = l
    while "Page$Next" in page and n < max_pages:
        f = champs_caches(page); f.update({"__EVENTTARGET": "GVConcoursPublic", "__EVENTARGUMENT": "Page$Next"})
        time.sleep(PAUSE)
        page = get(urllib.parse.urlencode(f).encode()); n += 1
        for l in lignes(page): vus[l["id"]] = l
    return list(vus.values()), n


def fusionner(anciens, nouveaux, jour):
    """Garde l'historique : date de première apparition et changements d'état des résultats."""
    par_id = {a["id"]: a for a in anciens}
    for c in nouveaux:
        a = par_id.get(c["id"])
        # 1re lecture du site (aucun ancien concours) : pas de date d'apparition, sinon tout paraîtrait « nouveau »
        c["vu_le"] = a.get("vu_le", jour) if a else (jour if par_id else "")
        hist = list(a.get("historique", [])) if a else []
        for cle in ("resultat_initial", "resultat_final"):
            if a and a.get(cle) != c.get(cle):
                hist.append({"le": jour, "champ": cle, "avant": a.get(cle, ""), "apres": c.get(cle, "")})
        c["historique"] = hist
        c["lien"] = c.get("lien") if c.get("source") == "finances" else URL
    return nouveaux


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pages", type=int, default=MAX_PAGES)
    ap.add_argument("--fichier", help="page HTML enregistrée (tests, sans réseau)")
    ap.add_argument("--finances-fichier", help="page enregistrée de la plateforme des Finances (tests) ; « non » = ne pas la lire")
    ap.add_argument("--sortie", default=SORTIE)
    ap.add_argument("--aujourdhui", default=dt.date.today().isoformat())
    a = ap.parse_args()
    if a.fichier:
        nouveaux, pages = lignes(open(a.fichier, encoding="utf-8").read()), 1
    else:
        nouveaux, pages = lire_portail(a.max_pages)
    ancien = json.load(open(a.sortie, encoding="utf-8")) if os.path.exists(a.sortie) else {"concours": []}
    if not nouveaux or (len(ancien["concours"]) >= 20 and len(nouveaux) < SEUIL_CHUTE * len(ancien["concours"])):
        print(f"ÉCHEC : lecture suspecte ({len(nouveaux)} lignes contre {len(ancien['concours'])} la fois précédente) ; ancien fichier gardé.")
        sys.exit(1)
    # deuxième source : ministère des Finances (une panne ne bloque rien : ses concours de la veille sont gardés)
    limite = (dt.date.fromisoformat(a.aujourdhui) - dt.timedelta(days=JOURS_FERMES_FINANCES)).isoformat()
    try:
        if a.finances_fichier == "non" or (a.fichier and not a.finances_fichier):
            fin = []
        elif a.finances_fichier:
            fin = F.lignes(open(a.finances_fichier, encoding="utf-8").read(), metier)
        else:
            fin = F.lire(metier)
        fin = [c for c in fin if not c["cloture_candidatures"] or c["cloture_candidatures"] >= limite]
        # même concours déjà sur le portail (Finances, même date limite) : on garde celui du portail
        deja = {(c["cloture_candidatures"]) for c in nouveaux if "المالية" in c["organisme"]}
        fin = [c for c in fin if c["cloture_candidatures"] not in deja]
        print(f"Ministère des Finances : {len(fin)} concours repris")
    except Exception as e:
        fin = [c for c in ancien["concours"] if c.get("source") == "finances"]
        print(f"ÉCHEC (non bloquant) : plateforme des Finances illisible ({str(e)[:120]}) ; {len(fin)} concours de la veille gardés")
    nouveaux = nouveaux + fin
    donnees = {"source": URL, "lu_le": a.aujourdhui, "pages": pages,
               "concours": sorted(fusionner(ancien["concours"], nouveaux, a.aujourdhui), key=lambda c: (c["cloture_candidatures"] or "9999", c["id"]))}
    os.makedirs(os.path.dirname(a.sortie), exist_ok=True)
    json.dump(donnees, open(a.sortie, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    par_metier = {}
    for c in nouveaux: par_metier[c["metier"]] = par_metier.get(c["metier"], 0) + 1
    print(f"{len(nouveaux)} concours lus sur {pages} page(s) ; par métier : {par_metier}")


if __name__ == "__main__":
    main()
