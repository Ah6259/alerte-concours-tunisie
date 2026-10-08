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

print(f"\n{ok}/{ok + ko} vérifications réussies" + (" — tout est bon." if not ko else f" — {ko} ÉCHEC(S)"))
sys.exit(1 if ko else 0)
