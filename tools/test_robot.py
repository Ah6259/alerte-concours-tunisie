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
    check("date de première apparition conservée", c0["vu_le"] == "2026-10-08")
    # panne : l'ancien fichier compte 40 lignes, la nouvelle lecture 5 → refus
    d2["concours"] = d2["concours"] * 8; json.dump(d2, open(sortie, "w", encoding="utf-8"), ensure_ascii=False)
    r3 = run("2026-10-10")
    check("panne du portail (beaucoup moins de lignes) : ancien fichier gardé, sortie en erreur", r3.returncode == 1 and len(json.load(open(sortie, encoding="utf-8"))["concours"]) == 40)

print(f"\n{ok}/{ok + ko} vérifications réussies" + (" — tout est bon." if not ko else f" — {ko} ÉCHEC(S)"))
sys.exit(1 if ko else 0)
