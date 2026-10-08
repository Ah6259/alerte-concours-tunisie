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

print(f"\n{ok}/{ok + ko} vérifications réussies" + (" — tout est bon." if not ko else f" — {ko} ÉCHEC(S)"))
sys.exit(1 if ko else 0)
