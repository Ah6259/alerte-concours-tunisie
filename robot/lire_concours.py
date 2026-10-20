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
DUREE_MAX = 10 * 60       # 14/10/2026 : portail très lent -> on garde ce qui est lu après 10 min (l'étape avait dépassé 15 min)
JOURS_FERMES_FINANCES = 60  # concours des Finances clos depuis plus longtemps : pas repris
JOURS_ABSENT = 3          # un concours ouvert qui manque à la lecture est gardé 3 jours
REPRISE_ATTENTE = 120       # lecture suspecte : nouvel essai après 2 min, puis 4 min (20/10/2026)
REPRISE_BUDGET = 8 * 60     # ... seulement si tout tient en 8 min (étape GitHub limitée à 15 min)
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


def lire_portail(max_pages, duree_max=DUREE_MAX, horloge=time.monotonic):
    debut = horloge()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def get(data=None):
        req = urllib.request.Request(URL, data=data, headers={"User-Agent": AGENT})
        for essai in range(3):
            try:
                with op.open(req, timeout=30) as r:
                    return r.read().decode("utf-8", "ignore")
            except Exception:
                if essai == 2: raise
                time.sleep(10 * (essai + 1))
    page = get(); vus = {}; n = 1
    for l in lignes(page): vus[l["id"]] = l
    while "Page$Next" in page and n < max_pages:
        if horloge() - debut > duree_max:      # trop lent : on s'arrête là ; les concours non relus sont gardés 3 jours (fusionner)
            print(f"Portail trop lent : lecture arrêtée après {n} page(s) ({int(horloge() - debut)} s), concours manquants gardés 3 jours")
            break
        f = champs_caches(page); f.update({"__EVENTTARGET": "GVConcoursPublic", "__EVENTARGUMENT": "Page$Next"})
        time.sleep(PAUSE)
        donnees = urllib.parse.urlencode(f).encode()
        page = get(donnees); n += 1
        # page vide ou coupée (08/10/2026 : lecture arrêtée à la 8e page, 37 lignes au lieu de 143) : on la redemande
        # jusqu'à 3 fois ; une vraie dernière page (moins de 5 lignes, pas de page suivante) revient pareille et est gardée
        meilleure = page
        for essai in range(3):
            if "Page$Next" in page or len(lignes(page)) >= 5:
                break
            time.sleep(10 * (essai + 1))
            page = get(donnees)
            if len(lignes(page)) >= len(lignes(meilleure)) or "Page$Next" in page:
                meilleure = page
        page = meilleure
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
        c["lu_le"] = jour
    # concours encore ouvert absent de la lecture du jour (portail qui coupe la liste : 08/10/2026, 75 lignes sur 143) :
    # gardé tel quel JOURS_ABSENT jours (date de sa dernière lecture dans « lu_le »), puis retiré
    vus = {c["id"] for c in nouveaux}
    limite = (dt.date.fromisoformat(jour) - dt.timedelta(days=JOURS_ABSENT)).isoformat()
    for a in anciens:
        ouvert = not a.get("cloture_candidatures") or a["cloture_candidatures"] >= jour
        if a["id"] not in vus and ouvert and a.get("lu_le", jour) >= limite:
            nouveaux.append(dict(a, lu_le=a.get("lu_le", jour)))
    return nouveaux


def suspecte(nouveaux, nb_ancien):
    return not nouveaux or (nb_ancien >= 20 and len(nouveaux) < SEUIL_CHUTE * nb_ancien)


def lire_avec_reprise(lire, nb_ancien, essais=3, attente=REPRISE_ATTENTE, dormir=time.sleep, horloge=time.monotonic,
                      budget=REPRISE_BUDGET):
    """20/10/2026 : le portail a coupé sa liste une fois (35 lignes au lieu de 100) et le robot est passé au rouge pour une
    panne de quelques minutes (la relance suivante était bonne). Une lecture suspecte est refaite (jusqu'à 3 fois, quelques
    minutes d'écart) ; la meilleure est gardée. Le rouge ne reste que si le portail coupe la liste à chaque essai.
    Pas de nouvel essai au-delà de REPRISE_BUDGET (l'étape GitHub est arrêtée à 15 min)."""
    debut = horloge()
    meilleure = lire()
    for essai in range(1, essais):
        if not suspecte(meilleure[0], nb_ancien) or horloge() - debut + attente * essai > budget:
            break
        print(f"Lecture suspecte ({len(meilleure[0])} lignes contre {nb_ancien}) : nouvel essai dans {attente * essai} s")
        dormir(attente * essai)
        autre = lire()
        if len(autre[0]) > len(meilleure[0]):
            meilleure = autre
    return meilleure


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
        nouveaux, pages = None, 0
    ancien = json.load(open(a.sortie, encoding="utf-8")) if os.path.exists(a.sortie) else {"concours": []}
    nb_ancien = len([c for c in ancien["concours"] if c.get("source") != "finances"])   # même source que la lecture
    if nouveaux is None:
        nouveaux, pages = lire_avec_reprise(lambda: lire_portail(a.max_pages), nb_ancien)
    if suspecte(nouveaux, nb_ancien):
        print(f"ÉCHEC : lecture suspecte ({len(nouveaux)} lignes contre {nb_ancien} la fois précédente) ; ancien fichier gardé.")
        sys.exit(1)
    # deuxième source : ministère des Finances (une panne ne bloque rien : ses concours de la veille sont gardés)
    limite = (dt.date.fromisoformat(a.aujourdhui) - dt.timedelta(days=JOURS_FERMES_FINANCES)).isoformat()
    # date de la dernière lecture réussie des Finances (tools/sources_en_panne.py : ÉCHEC après 2 jours, 15/10/2026)
    finances_ok = ancien.get("finances_ok") or a.aujourdhui
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
        if a.finances_fichier != "non" and not (a.fichier and not a.finances_fichier):
            finances_ok = a.aujourdhui
    except Exception as e:
        fin = [c for c in ancien["concours"] if c.get("source") == "finances"]
        print(f"ÉCHEC (non bloquant) : plateforme des Finances illisible ({str(e)[:120]}) ; {len(fin)} concours de la veille gardés")
    nouveaux = nouveaux + fin
    donnees = {"source": URL, "lu_le": a.aujourdhui, "finances_ok": finances_ok, "pages": pages,
               "concours": sorted(fusionner(ancien["concours"], nouveaux, a.aujourdhui), key=lambda c: (c["cloture_candidatures"] or "9999", c["id"]))}
    os.makedirs(os.path.dirname(a.sortie), exist_ok=True)
    json.dump(donnees, open(a.sortie, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    par_metier = {}
    for c in nouveaux: par_metier[c["metier"]] = par_metier.get(c["metier"], 0) + 1
    print(f"{len(nouveaux)} concours lus sur {pages} page(s) ; par métier : {par_metier}")


if __name__ == "__main__":
    main()
