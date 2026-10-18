"""Test du robot (sans réseau) : python tools/test_robot.py"""
import json, os, subprocess, sys, tempfile
sys.stdout.reconfigure(encoding="utf-8")
ICI = os.path.dirname(os.path.abspath(__file__)); RACINE = os.path.dirname(ICI)
sys.path.insert(0, os.path.join(RACINE, "robot"))
import lire_concours as R

ok = 0; ko = 0
def check(nom, cond):
    global ok, ko
    print(("OK   " if cond else "ÉCHEC ") + nom); ok += bool(cond); ko += (not cond)

page = open(os.path.join(ICI, "exemples", "portail-page1.html"), encoding="utf-8").read()
L = R.lignes(page)
check("page officielle enregistrée : 5 lignes de concours lues", len(L) == 5)
check("chaque ligne : numéro, organisme, grade, postes, dates ISO", all(l["id"].isdigit() and l["organisme"] and l["grade"] and isinstance(l["postes"], int)
      and len(l["cloture_candidatures"]) == 10 for l in L))
check("état des résultats lu (« لم تنشر » = pas encore publié)", any("تنشر" in l["resultat_initial"] for l in L))
for grade, attendu in [("مهندس اول جيولوجيا", "ingenieur"), ("عامل متعاقد صنف 5 يشغل خطة سائق في الوزن الثقيل", "chauffeur"),
                       ("مستكتب إدارة", "administratif"), ("تقني سام", "technicien"), ("ممرض", "sante"), ("أستاذ تعليم ثانوي", "enseignant"),
                       ("عامل متعاقد صنف 5 يشغل خطة سباك", "ouvrier"), ("رسام", "autre")]:
    check(f"métier : « {grade} » → {attendu}", R.metier(grade) == attendu)
import gouvernorats as G
for org, attendu in [("بلدية الحمامات", "nabeul"), ("بلدية دارعلوش", "nabeul"), ("بلدية وادي الليل", "manouba"), ("بلدية رقادة", "kairouan"),
                     ("بلدية قلعة سنان", "le-kef"), ("وكالة التعمير لتونس الكبرى", "tunis"), ("الإدارة الجهوية للصحة بتونس", "tunis"),
                     ("المندوبية الجهوية للتربية بصفاقس", "sfax"), ("الشركة الوطنية العقارية للبلاد التونسية", "national"),
                     ("الديوان الوطني للمناجم", "national"), ("وزارة الداخلية", "national")]:
    check(f"gouvernorat : « {org} » → {attendu}", G.gouvernorat(org) == attendu)
check("chaque ligne lue a un gouvernorat (ou « national »)", all(l["gouvernorat"] in G.NOMS for l in L))
check("chiffres arabes ٢٠٢٦-١١-١٠ → 2026-11-10", R.date_iso("٢٠٢٦-١١-١٠") == "2026-11-10")

with tempfile.TemporaryDirectory() as d:
    f = os.path.join(d, "page.html"); open(f, "w", encoding="utf-8").write(page)
    sortie = os.path.join(d, "concours.json")
    run = lambda jour: subprocess.run([sys.executable, os.path.join(RACINE, "robot", "lire_concours.py"), "--fichier", f, "--sortie", sortie, "--aujourdhui", jour], capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    r1 = run("2026-10-08")
    check("1re lecture : fichier écrit", r1.returncode == 0 and len(json.load(open(sortie, encoding="utf-8"))["concours"]) == 5)
    d1 = json.load(open(sortie, encoding="utf-8"))
    # un résultat publié entre deux lectures → historique
    d1["concours"][0]["resultat_initial"] = "ancien état"; json.dump(d1, open(sortie, "w", encoding="utf-8"), ensure_ascii=False)
    run("2026-10-09"); d2 = json.load(open(sortie, encoding="utf-8"))
    c0 = [c for c in d2["concours"] if c["id"] == d1["concours"][0]["id"]][0]
    check("historique : un changement de l'état des résultats est gardé avec sa date", any(h["le"] == "2026-10-09" and h["champ"] == "resultat_initial" for h in c0["historique"]))
    check("1re lecture du site : pas de date d'apparition (rien ne paraît « nouveau »), et elle est conservée", c0["vu_le"] == "")
    d3 = json.load(open(sortie, encoding="utf-8")); d3["concours"] = d3["concours"][1:]; json.dump(d3, open(sortie, "w", encoding="utf-8"), ensure_ascii=False)
    run("2026-10-11"); d4 = json.load(open(sortie, encoding="utf-8"))
    check("un concours apparu après la 1re lecture reçoit sa date d'apparition", [c for c in d4["concours"] if c["id"] == d1["concours"][0]["id"]][0]["vu_le"] == "2026-10-11")
    d2 = d4
    # panne : l'ancien fichier compte 40 lignes, la nouvelle lecture 5 → refus
    d2["concours"] = d2["concours"] * 8; json.dump(d2, open(sortie, "w", encoding="utf-8"), ensure_ascii=False)
    r3 = run("2026-10-10")
    check("panne du portail (beaucoup moins de lignes) : ancien fichier gardé, sortie en erreur", r3.returncode == 1 and len(json.load(open(sortie, encoding="utf-8"))["concours"]) == 40)

# --- actualités du portail (08/10/2026)
import lire_actualites as A
x = A.lire_detail(open(os.path.join(ICI, "exemples", "portail-actualite-333.html"), encoding="utf-8").read(), 333)
check("actualité enregistrée : organisme, date ISO, résumé court (jamais le texte entier), lien officiel", x and x["organisme"] == "الديوان الوطني للتطهير"
      and x["date"] == "2026-10-07" and 50 < len(x["resume"]) <= A.RESUME + 1 and x["lien"].startswith("https://www.concours.gov.tn/P1/index31.aspx?id=333"))
check("actualité : « يعتزم … فتح مناظرة » → nouveau concours", x and x["type"] == "nouveau")
for t, attendu in [("تعلن الشركة عن القائمات النهائيّة للمقبولين بالاختبارات الشفاهية", "resultats"), ("تم نشر القائمة النهائية للناجحين", "resultats"),
                   ("يعلم المركز كافة المترشحين الذين تم قبول ترشحاتهم أوليا", "candidatures"), ("استدعاء المترشحين لاجتياز الاختبار الكتابي", "convocation"),
                   ("تأجيل موعد الاختبار الكتابي", "report"), ("بلاغ إلى العموم", "autre")]:
    check(f"type d'actualité : « {t[:40]} » → {attendu}", A.type_de(t) == attendu)
check("page qui n'est pas une actualité → ignorée", A.lire_detail("<html><body>rien</body></html>", 1) is None)
r = A.rattacher([{"organisme": "بلدية رقادة"}], [{"organisme": "بلديّة رقاده", "id": "3155"}, {"organisme": "بلدية رقادة", "id": "3156"}])
check("actualité rattachée aux concours du même organisme (à la chadda et au ة près)", r[0]["concours"] == ["3155", "3156"])

# --- page coupée par le portail (08/10/2026 : 37 lignes au lieu de 143) : la page vide est redemandée
import io, urllib.request as U
class _Rep(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False
_suite = [page if "Page$Next" in page else page + "Page$Next", "<html>erreur passagère</html>",
          page.replace("Page$Next", "").replace(f">{L[0]['id']}<", ">7777<")]
class _Op:
    def open(self, req, timeout=0): return _Rep(_suite.pop(0).encode())
_vrai, _pause, _dormir = U.build_opener, R.PAUSE, R.time.sleep
U.build_opener = lambda *a: _Op(); R.PAUSE = 0; R.time.sleep = lambda s: None
try:
    lu, n = R.lire_portail(10)
finally:
    U.build_opener, R.PAUSE, R.time.sleep = _vrai, _pause, _dormir
check("page vide renvoyée par le portail : redemandée, la lecture continue (rien de perdu)", n == 2 and not _suite and len(lu) >= 6)
# --- portail très lent (14/10/2026 : étape arrêtée à 15 min) : au-delà de DUREE_MAX, on garde les pages déjà lues
_suite = [page if "Page$Next" in page else page + "Page$Next"] * 5
_t = iter([0, 1, 700, 700, 700, 700])
U.build_opener = lambda *a: _Op(); R.PAUSE = 0; R.time.sleep = lambda s: None
try:
    lu, n = R.lire_portail(10, duree_max=600, horloge=lambda: next(_t))
finally:
    U.build_opener, R.PAUSE, R.time.sleep = _vrai, _pause, _dormir
check("portail trop lent : lecture arrêtée après 10 min avec les pages déjà lues (plus d'étape coupée à 15 min)", n == 2 and len(lu) == len(R.lignes(page)) > 0)

# --- portail des actualités qui ne répond plus (08/10/2026 : étape bloquée 20 min) : arrêt après 3 échecs de suite
appels = []
def _get(url):
    appels.append(url)
    if url == A.LISTE: return "".join(f'<a href="index31.aspx?id={n}">x</a>' for n in range(1, 30))
    raise OSError("délai dépassé")
_g, _p, _argv = A.get, A.PAUSE, sys.argv
with tempfile.TemporaryDirectory() as d:
    sortie = os.path.join(d, "actualites.json")
    json.dump({"actualites": [{"id": "999", "organisme": "x", "date": "2026-10-01", "resume": "بلاغ", "lien": "https://www.concours.gov.tn/"}]}, open(sortie, "w", encoding="utf-8"))
    A.get, A.PAUSE, sys.argv = _get, 0, ["lire_actualites.py", "--sortie", sortie]
    try:
        import contextlib, io as _io
        with contextlib.redirect_stdout(_io.StringIO()):
            A.main()
    finally:
        A.get, A.PAUSE, sys.argv = _g, _p, _argv
    check("actualités : portail en panne → arrêt après 3 échecs de suite (pas 29 attentes), ancien fichier gardé",
          len(appels) == 4 and json.load(open(sortie, encoding="utf-8"))["actualites"][0]["id"] == "999")

# --- relevé de l'ANETI depuis le PC d'Ahmed (tools/aneti_pc.py, 08/10/2026) : sans réseau
sys.path.insert(0, ICI)
import aneti_pc as P, pathlib
with tempfile.TemporaryDirectory() as d:
    P.SORTIE, P.PAUSE = pathlib.Path(d), 0
    vus_url = []
    def _faux(url):
        vus_url.append(url)
        if url.endswith("page=21"):
            return 200, "".join(f'<a href="global.php?page=198&amp;ref={n}">x</a>' for n in range(1, 60)) + '<a href="global.php?page=198&amp;ref=1">bis</a>'
        if "ref=7" in url: raise OSError("coupé")
        return 200, f"<p>détail {url}</p>"
    P.telecharger = _faux
    r = P.relever({"pages": [{"nom": "concours-fr", "url": "https://www.emploi.nat.tn/fo/Fr/global.php?page=21", "suivre": "global\\.php\\?page=198&(?:amp;)?ref=\\d+", "max": 40}]})
    check("ANETI (PC) : la liste + 40 détails au plus (liens en double ignorés), adresses complètes, une page en panne n'arrête pas le relevé",
          len(vus_url) == 41 and vus_url[1] == "https://www.emploi.nat.tn/fo/Fr/global.php?page=198&ref=1" and len(set(vus_url)) == 41
          and sum("erreur" in x for x in r["pages"]) == 1 and (pathlib.Path(d) / "concours-fr-detail-3.html").exists() and (pathlib.Path(d) / "releve.json").exists())

# --- concours ouvert absent de la lecture du jour (portail qui coupe la liste, 08/10/2026) : gardé 3 jours
base = [dict(l, cloture_candidatures="2026-12-31") for l in L]
f1 = R.fusionner([], [dict(x) for x in base], "2026-10-08")
f2 = R.fusionner(f1, [dict(x) for x in base[1:]], "2026-10-09")
f3 = R.fusionner(f2, [dict(x) for x in base[1:]], "2026-10-12")
clos = R.fusionner([dict(base[0], cloture_candidatures="2026-10-01", lu_le="2026-10-08")], [], "2026-10-09")
check("concours ouvert qui manque un jour : gardé (avec sa date de lecture), retiré après 3 jours d'absence ; un concours clos n'est pas gardé",
      len(f2) == 5 and [c for c in f2 if c["id"] == base[0]["id"]][0]["lu_le"] == "2026-10-08" and len(f3) == 4 and clos == [])

# --- veille hebdomadaire des sites des ministères (08/10/2026) : sans réseau
import veille_ministeres as V
V.PAUSE = 0
_acc = ('<a href="/actualite/1">إعلان فتح مناظرة خارجية بالإختبارات لإنتداب نظار أمن بعنوان سنة 2026</a>'
        '<a href="/fr/concours">المناظرات</a><a href="/contact">اتصل بنا</a>'
        '<a href="/a/2">RÈGLEMENT DU CONCOURS ARTISTIQUE L’ART AU SERVICE DE LA LAGUNE</a>'
        '<a href="/a/3">Avis concernant le concours externe pour le recrutement des ingénieurs principaux</a>')
_rub = '<a href="/actualite/9">قائمة المترشحين المدعوين لاجتياز الاختبار الكتابي للمناظرة الخارجية</a>'
_pages = {"https://www.exemple.gov.tn/": _acc, "https://www.exemple.gov.tn/fr/concours": _rub}
st, ann, err = V.veiller({"url": "https://www.exemple.gov.tn/"}, lambda u: (u, _pages[u]))
check("ministères : annonces de l'accueil + celles de la rubrique « المناظرات » (lue aussi), liens complets, concours artistique écarté",
      st == "ok" and [u for u, _ in ann] == ["https://www.exemple.gov.tn/actualite/1", "https://www.exemple.gov.tn/a/3", "https://www.exemple.gov.tn/actualite/9"])
st, ann, err = V.veiller({"url": "https://x.gov.tn/"}, lambda u: (_ for _ in ()).throw(OSError("connection reset")))
check("ministères : liens mal écrits par le site corrigés ou écartés", V.liens('<a href="http://\nhttp://x.gov.tn/a">Formulaires utiles</a><a href="/p/{$page->slug}">مطلب</a>', "https://x.gov.tn/") == [("http://x.gov.tn/a", "Formulaires utiles")])
check("ministères : site injoignable → noté, rien de cassé", st == "injoignable" and ann == [] and "reset" in err)
st, ann, err = V.veiller({"url": "https://x.gov.tn/"}, lambda u: (u, "<title>Just a moment...</title>"))
check("ministères : protection anti-robot → noté « bloqué », pas de contournement", st == "bloque")
_d = ('<a href="/f/demande-acces.pdf">تحميل مطلب نفاذ إلى المعلومة</a><a href="/formulaires">Formulaires</a>'
      '<a href="/a/5">مشروع نموذجي لدعم الحرفيين وتثمين الموارد المحلية بالجهة</a>')
_pd = {"https://www.exemple.gov.tn/": _d, "https://www.exemple.gov.tn/formulaires": '<a href="/f/attestation.pdf">Attestation de travail</a>'}
_docs = []
V.veiller({"url": "https://www.exemple.gov.tn/"}, lambda u: (u, _pd[u]), _docs)
check("ministères : documents officiels relevés pour le site Documents (PDF de l'accueil + rubrique « Formulaires »), « نموذجي » écarté",
      [u for u, _ in _docs] == ["https://www.exemple.gov.tn/f/demande-acces.pdf", "https://www.exemple.gov.tn/f/attestation.pdf"])

# --- 2e source : plateforme des concours du ministère des Finances (08/10/2026)
import lire_finances as F
fin = F.lignes(open(os.path.join(ICI, "exemples", "finances.html"), encoding="utf-8").read(), R.metier)
check("Finances : 6 concours lus (les blocs de résultats ignorés), une ligne par grade", len(fin) == 6 and not any("الناجحين" in c["grade"] for c in fin))
check("Finances : numéros stables 900000+ (jamais ceux du portail), uniques", all(c["id"].isdigit() and int(c["id"]) >= 900000 for c in fin) and len({c["id"] for c in fin}) == 6
      and fin[0]["id"] == "900900")
check("Finances : grade + spécialités, postes, dates ISO, national, lien vers l'avis officiel (PDF)",
      fin[0]["grade"].startswith("متفقدين") and "محاسبة" in fin[0]["grade"] and fin[0]["postes"] == 434 and fin[0]["cloture_candidatures"] == "2026-09-10"
      and fin[0]["ouverture_candidatures"] == "2026-08-20" and all(c["gouvernorat"] == "national" and c["organisme"] == "وزارة المالية" for c in fin)
      and fin[0]["lien"] == "https://concours.finances.gov.tn/theme/documents/concours/9/avis-concours.pdf")
check("Finances : métiers (inspecteurs → finances, techniciens → techniciens)", fin[0]["metier"] == "finance" and fin[2]["metier"] == "technicien")
with tempfile.TemporaryDirectory() as d:
    f = os.path.join(d, "page.html"); open(f, "w", encoding="utf-8").write(page)
    sortie = os.path.join(d, "concours.json")
    run = lambda jour, ff: subprocess.run([sys.executable, os.path.join(RACINE, "robot", "lire_concours.py"), "--fichier", f, "--finances-fichier", ff, "--sortie", sortie, "--aujourdhui", jour], capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    r = run("2026-10-08", os.path.join(ICI, "exemples", "finances.html")); cs = json.load(open(sortie, encoding="utf-8"))["concours"]
    ff = [c for c in cs if c.get("source") == "finances"]
    check("lecture complète : portail (5) + Finances clos depuis moins de 60 jours (2 ; ceux d'août et de 2024 écartés), lien gardé",
          r.returncode == 0 and len(cs) == 7 and len(ff) == 2 and all(c["lien"].startswith(F.URL) for c in ff))
    r = run("2026-10-09", os.path.join(d, "absent.html")); cs = json.load(open(sortie, encoding="utf-8"))["concours"]
    check("plateforme des Finances en panne : non bloquant, ses concours de la veille gardés", r.returncode == 0 and len([c for c in cs if c.get("source") == "finances"]) == 2
          and "ÉCHEC (non bloquant)" in r.stdout)
    d_fin = json.load(open(sortie, encoding="utf-8"))
    check("Finances en panne : la date de dernière lecture réussie n'avance pas (alerte après 2 jours)", d_fin.get("finances_ok") == "2026-10-08")

# --- 15/10/2026 (§ 17) : aucune source en panne qui reste invisible (robot vert)
try:
    F.lignes("<html><body>Nouvelle présentation du site</body></html>")
    check("Finances : page sans aucun bloc d'annonce = panne (pas « 0 concours » en vert)", False)
except ValueError:
    check("Finances : page sans aucun bloc d'annonce = panne (pas « 0 concours » en vert)", True)
sys.path.insert(0, os.path.join(RACINE, "tools"))
import sources_en_panne as SP
check("alerte : Finances sans lecture réussie depuis 3 jours -> ÉCHEC ; 2 jours -> rien",
      [s for s, _ in SP.en_panne({"lu_le": "2026-10-15", "finances_ok": "2026-10-12"}, {"lu_le": "2026-10-15"}, "2026-10-15")] == ["plateforme du ministère des Finances"]
      and SP.en_panne({"lu_le": "2026-10-15", "finances_ok": "2026-10-13"}, {"lu_le": "2026-10-13"}, "2026-10-15") == [])
check("alerte : actualités jamais lues -> ÉCHEC", any("actualités" in s for s, _ in SP.en_panne({"lu_le": "2026-10-15", "finances_ok": "2026-10-15"}, {}, "2026-10-15")))

# --- Rapports du mois (18/10/2026, règle commune § 25) : chiffres = comptages, mois fini figé, pas de fausse évolution
import rapports as RAP, construire_site as CS
def _c(i, g, p, vu, lim, m="ouvrier", org=None, hist=()):
    return {"id": str(i), "gouvernorat": g, "postes": p, "vu_le": vu, "cloture_candidatures": lim, "metier": m,
            "organisme": org or f"org{i}", "grade": "g", "historique": list(hist)}
base = [_c(1, "national", 3, "", "2026-11-30", "ingenieur"), _c(2, "nabeul", 2, "2026-10-12", "2026-10-20"),
        _c(3, "tunis", 4, "2026-10-12", "2026-10-05"), _c(4, "sousse", None, "2026-10-08", "2026-12-01"),
        _c(5, "bizerte", 1, "2026-10-14", "2026-11-10", hist=[{"le": "2026-10-14", "champ": "resultat_initial", "avant": "لم تنشر", "apres": "اطلاع"}])]
actus = [{"date": "2026-10-03", "type": "resultats"}, {"date": "2026-10-14", "type": "nouveau"}, {"date": "2026-09-30", "type": "nouveau"}, {"date": "2026-10-16", "type": "nouveau"}]
k, _ = RAP.calculer(base, actus, "2026-10-15")
check("rapport : concours ouverts = même règle que l'accueil (4 ouverts, 6 postes, 1 sans nombre de postes)", k["ouverts"] == {"n": 4, "postes": 6, "sans_postes": 1})
check("rapport : nationaux 1 / locaux 3, 3 gouvernorats, clôture sous 7 jours = 1", k["national"]["n"] == 1 and k["locaux"]["n"] == 3 and len(k["gouvernorats"]) == 3 and k["semaine"]["n"] == 1)
check("rapport : nouveaux = apparus après le 1er jour de lecture ET encore ouverts (1 clos et 1 du 08/10 écartés)", k["nouveaux"]["n"] == 2 and k["debut"] == "2026-10-09")
check("rapport : inscriptions closes ce mois = 1 ; résultat publié vu par le robot = 1 ; avis du mois jusqu'au jour des chiffres = 2",
      k["clos"]["n"] == 1 and k["resultats"] == {"initial": 1, "final": 0} and k["avis"]["n"] == 2)
check("rapport : aucun organisme classé sous 3 concours ouverts", k["organismes"] == [])
k3, _ = RAP.calculer([_c(10 + i, "tunis", 1, "", "2026-12-01", org=f"o{i % 3}") for i in range(9)], [], "2026-10-15")
k2, _ = RAP.calculer([_c(10 + i, "tunis", 1, "", "2026-12-01", org=f"o{i % 2}") for i in range(6)], [], "2026-10-15")
check("rapport : organismes classés seulement avec au moins 3 concours chacun", len(k3["organismes"]) == 3 and len(k2["organismes"]) == 2)
h1 = RAP.mettre_a_jour(None, base, actus, "2026-10-15")
h2 = RAP.mettre_a_jour(h1, [c for c in base if c["id"] != "3"], actus, "2026-10-20")
check("historique : concours retiré du tableau en cours de mois toujours compté (inscriptions closes), 1er jour gardé, dernière date avancée",
      h2["mois"]["2026-10"]["chiffres"]["clos"]["n"] == 1 and h2["mois"]["2026-10"]["premier_jour"] == "2026-10-15" and h2["mois"]["2026-10"]["dernier_jour"] == "2026-10-20")
oct_fige = json.dumps(h2["mois"]["2026-10"]["chiffres"], sort_keys=True)
autres = [_c(20 + i, "sfax", 5, "2026-11-01", "2026-12-15") for i in range(4)]
h3 = RAP.mettre_a_jour(h2, autres, [], "2026-11-02")
h4 = RAP.mettre_a_jour(h3, autres[:1], [], "2026-10-25")
h5 = RAP.mettre_a_jour(h4, autres[:2], [], "2026-11-05")
check("mois fini : figé au 1er passage du mois suivant, chiffres et date jamais modifiés ensuite (même avec d'autres données ou une date plus ancienne)",
      h3["mois"]["2026-10"]["fini"] and "vus" not in h3["mois"]["2026-10"] and h4 == h3 and h5["mois"]["2026-10"] == h3["mois"]["2026-10"]
      and json.dumps(h5["mois"]["2026-10"]["chiffres"], sort_keys=True) == oct_fige and h5["mois"]["2026-10"]["dernier_jour"] == "2026-10-20")
p1, d1 = RAP.pages(CS, h2, "v", "2026-10-20")
p5, d5 = RAP.pages(CS, h5, "v", "2026-11-05")
check("pages : rapports/ + rapports/2026-10/, date des chiffres pour le plan du site", set(p1) == {"rapports/", "rapports/2026-10/"} and d1["rapports/2026-10/"] == "2026-10-20")
check("1er mois : « Premier rapport », aucune évolution inventée", "Premier rapport" in p1["rapports/2026-10/"] and 'id="evolution"' not in p1["rapports/2026-10/"])
check("mois suivant : évolution depuis le mois précédent (ses chiffres au 20/10), mois précédent marqué « figés »",
      'id="evolution"' in p5["rapports/2026-11/"] and "au 20/10/2026" in p5["rapports/2026-11/"] and "figés" in p5["rapports/2026-10/"] and "Premier rapport" not in p5["rapports/2026-11/"])
check("pages des rapports : JSON-LD Article + FAQ + fil d'Ariane, « Citer ces chiffres », méthode, aucun trou",
      all('"@type": "Article"' in h and '"@type": "FAQPage"' in h and '"@type": "BreadcrumbList"' in h and 'id="citer"' in h and 'id="methode"' in h
          and "None" not in h and "undefined" not in h for c, h in p5.items() if c != "rapports/"))
check("rapports : UN bouton « Partager ce rapport » en haut et en bas (adresse de la page), signature, description qui commence par le nom du site, aucun lien Facebook / WhatsApp séparé",
      all(h.count("data-partage-rapport") == 2 and h.count(f'data-url="https://concours.clicvia.com/{c}"') == 2 and "rap-partage-haut" in h
          and "Un rapport d’<b>Alerte Concours Tunisie</b> · concours.clicvia.com" in h and '<meta name="description" content="Alerte Concours Tunisie — rapport du mois. ' in h
          and "Rapport du mois d’Alerte Concours Tunisie :" in h and "wa.me/" not in h and "sharer" not in h for c, h in p5.items()))
check("pas de classement sur 1 ou 2 éléments : pas de « gouvernorat qui compte le plus » avec 1 seul gouvernorat (novembre)",
      "Gouvernorat qui compte le plus" not in p5["rapports/2026-11/"] and "Gouvernorat qui compte le plus" in p1["rapports/2026-10/"])

print(f"\n{ok}/{ok + ko} vérifications réussies" + (" — tout est bon." if not ko else f" — {ko} ÉCHEC(S)"))
sys.exit(1 if ko else 0)
