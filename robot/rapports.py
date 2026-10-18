"""Rapports du mois d'Alerte Concours Tunisie (18/10/2026, demande d'Ahmed ; règle commune § 25).

Articles AUTOMATIQUES mais VRAIS : chaque phrase est un chiffre compté dans les données GRATUITES du site
(donnees/concours.json = tableau officiel des concours publics + plateforme des Finances ; donnees/actualites.json = avis
du portail). Aucune estimation, aucun texte inventé.

  python robot/rapports.py [--aujourdhui AAAA-MM-JJ]   (met à jour donnees/rapports.json ; appelé par maj.yml)

Historique (donnees/rapports.json) : mois -> {premier_jour, dernier_jour, fini, chiffres, vus}.
- Le mois des données (date « lu_le » du tableau) est recalculé à chaque passage : « chiffres au <dernier_jour> ».
- Un mois passé devient « fini » au premier passage du mois suivant : ses chiffres ne sont PLUS JAMAIS modifiés
  (la liste « vus » est alors retirée, elle ne sert qu'au mois en cours).
- « vus » = concours vus dans le tableau pendant le mois (un concours retiré du tableau en cours de mois reste compté
  dans « nouveaux » et « inscriptions closes »).
Les pages rapports/ et rapports/AAAA-MM/ sont fabriquées par construire_site.py (fonction pages() ci-dessous), en
lecture seule de l'historique."""
import argparse, datetime as dt, json, os, sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
HIST = os.path.join(RACINE, "donnees", "rapports.json")
DEBUT_SUIVI = "2026-10-08"   # 1re lecture du tableau officiel par notre robot (les concours présents ce jour-là n'ont pas de date d'apparition)
MIN_ORG = 3                  # un organisme n'est classé qu'avec au moins 3 concours ouverts
MIN_LIGNES = 3               # pas de classement sur 1 ou 2 éléments (règle commune § 22.4)
PUBLIE = "اطلاع"             # « consulter » dans la colonne des résultats = résultat publié
MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
NOM_SITE, NOM_SITE_AR, DOMAINE = "Alerte Concours Tunisie", "تنبيه المناظرات تونس", "concours.clicvia.com"
DESC_DEBUT = f"{NOM_SITE} — rapport du mois. "   # début de la meta description des rapports (aperçu Facebook / WhatsApp)
MOIS_AR = ["جانفي", "فيفري", "مارس", "أفريل", "ماي", "جوان", "جويلية", "أوت", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]


def nom_mois(m, ar=False):
    return f"{(MOIS_AR if ar else MOIS_FR)[int(m[5:7]) - 1]} {m[:4]}"


def de(mot):
    return ("d’" if mot[0] in "aeiouéèêh" else "de ") + mot


def ouvert(c, jour):
    """Même règle que l'accueil (construire_site.charger) : pas de date limite, ou date limite aujourd'hui ou plus tard."""
    return not c.get("cloture_candidatures") or c["cloture_candidatures"] >= jour


def _somme(cs):
    return {"n": len(cs), "postes": sum(c.get("postes") or 0 for c in cs), "sans_postes": sum(1 for c in cs if not c.get("postes"))}


def _resume(c, mois):
    """Ce qu'on garde d'un concours vu pendant le mois (pour les compteurs du mois)."""
    pubs = sorted({h["champ"] for h in c.get("historique", []) if str(h.get("le", ""))[:7] == mois
                   and PUBLIE in str(h.get("apres", "")) and PUBLIE not in str(h.get("avant", ""))})
    return {"postes": c.get("postes"), "metier": c.get("metier"), "gouvernorat": c.get("gouvernorat"),
            "cloture_candidatures": c.get("cloture_candidatures") or "", "vu_le": c.get("vu_le") or "", "publies": pubs}


def calculer(concours, actus, jour, vus=None):
    """Chiffres du mois de `jour` (date des données). Rend (chiffres, vus mis à jour)."""
    mois, debut = jour[:7], jour[:7] + "-01"
    vus = dict(vus or {})
    for c in concours:
        r = _resume(c, mois)
        a = vus.get(c["id"])
        if a and a.get("vu_le") and (not r["vu_le"] or a["vu_le"] < r["vu_le"]):
            r["vu_le"] = a["vu_le"]          # concours sorti puis revenu dans le tableau : sa 1re date d'apparition du mois est gardée
        if a:
            r["publies"] = sorted(set(r["publies"]) | set(a.get("publies", [])))
        vus[c["id"]] = r
    ouv = [c for c in concours if ouvert(c, jour)]
    fin7 = (dt.date.fromisoformat(jour) + dt.timedelta(days=6)).isoformat()
    semaine = [c for c in ouv if c.get("cloture_candidatures") and jour <= c["cloture_candidatures"] <= fin7]
    par = lambda cle, cs: {k: [c for c in cs if c.get(cle) == k] for k in sorted({c.get(cle) for c in cs})}
    gouvs = sorted(([g, len(cs), _somme(cs)["postes"]] for g, cs in par("gouvernorat", ouv).items() if g != "national"), key=lambda x: (-x[1], -x[2], x[0]))
    metiers = sorted(([m, len(cs), _somme(cs)["postes"]] for m, cs in par("metier", ouv).items()), key=lambda x: (-x[1], -x[2], x[0]))
    orgs = sorted(([o, len(cs), _somme(cs)["postes"], cs[0].get("gouvernorat")] for o, cs in par("organisme", ouv).items() if len(cs) >= MIN_ORG),
                  key=lambda x: (-x[1], -x[2], x[0]))
    v = list(vus.values())
    # nouveau = apparu dans le tableau APRÈS la toute 1re journée de lecture (08/10/2026 : lectures coupées, 2e source ajoutée)
    # et encore ouvert ce jour-là (un concours déjà clos qui réapparaît n'est pas un nouveau concours)
    debut_nv = max(debut, (dt.date.fromisoformat(DEBUT_SUIVI) + dt.timedelta(days=1)).isoformat())
    nouveaux = [x for x in v if x["vu_le"] and debut_nv <= x["vu_le"] <= jour and (not x["cloture_candidatures"] or x["cloture_candidatures"] >= x["vu_le"])]
    clos = [x for x in v if x["cloture_candidatures"] and debut <= x["cloture_candidatures"] < jour]
    av = [x for x in actus if str(x.get("date", ""))[:7] == mois and x["date"] <= jour]
    types = {}
    for x in av:
        types[x.get("type", "autre")] = types.get(x.get("type", "autre"), 0) + 1
    chiffres = {
        "au": jour, "debut": debut_nv,
        "ouverts": _somme(ouv),
        "national": _somme([c for c in ouv if c.get("gouvernorat") == "national"]),
        "locaux": _somme([c for c in ouv if c.get("gouvernorat") != "national"]),
        "finances": sum(1 for c in ouv if c.get("source") == "finances"),
        "gouvernorats": gouvs, "metiers": metiers, "organismes": orgs,
        "semaine": dict(_somme(semaine), jusqu_au=fin7),
        "nouveaux": _somme(nouveaux),
        "nouveaux_metiers": sorted(([m, len(cs)] for m, cs in par("metier", nouveaux).items()), key=lambda x: (-x[1], x[0])),
        "clos": _somme(clos),
        "resultats": {"initial": sum(1 for x in v if "resultat_initial" in x["publies"]), "final": sum(1 for x in v if "resultat_final" in x["publies"])},
        "avis": {"n": len(av), "types": types},
    }
    return chiffres, vus


def mettre_a_jour(hist, concours, actus, jour):
    """Met à jour l'historique pour le mois de `jour`. Un mois fini n'est jamais modifié ; une date plus ancienne que le
    dernier mois connu ne change rien."""
    hist = json.loads(json.dumps(hist or {"mois": {}}))
    mois = jour[:7]
    for m, e in hist["mois"].items():
        if m < mois and not e.get("fini"):
            e["fini"] = True
            e.pop("vus", None)
    e = hist["mois"].get(mois)
    if (e and e.get("fini")) or any(m > mois for m in hist["mois"]) or (e and e.get("dernier_jour", "") > jour):
        return hist
    e = e or {"premier_jour": jour}
    chiffres, vus = calculer(concours, actus, jour, e.get("vus"))
    e.update(dernier_jour=jour, fini=False, chiffres=chiffres, vus=vus)
    hist["mois"][mois] = e
    hist["mois"] = dict(sorted(hist["mois"].items()))
    return hist


def charger_hist(f=HIST):
    return json.load(open(f, encoding="utf-8")) if os.path.exists(f) else {"mois": {}}


# ------------------------------------------------------------------ pages (appelées par construire_site.py)
def _nb(n):
    return f"{n:,}".replace(",", " ")


def _postes(n, ar=False, C=None):
    if ar:
        return f"{C.ISO(_nb(n))} {'خطة' if n == 1 else 'خطط'}"
    return f"{_nb(n)} poste{'s' if n > 1 else ''}"


def _table(C, entetes, lignes):
    th = "".join(f'<th scope="col">{C.L(fr, ar)}</th>' for fr, ar in entetes)
    return f'<div class="rap-tableau"><table class="rap-table"><thead><tr>{th}</tr></thead><tbody>{"".join(lignes)}</tbody></table></div>'


def signature(C):
    """« Un rapport d'Alerte Concours Tunisie · concours.clicvia.com », sous le titre (18/10/2026, demande d'Ahmed)."""
    return (f'    <p class="rap-signature">' + C.L(f"Un rapport d’<b>{NOM_SITE}</b> · {DOMAINE}", f"تقرير من <b>{NOM_SITE_AR}</b> · <bdi dir=\"ltr\">{DOMAINE}</bdi>") + "</p>")


def bloc_partage(C, titre, chemin, haut=False):
    """UN SEUL bouton « Partager ce rapport » (menu de partage du téléphone : Facebook, WhatsApp, LinkedIn…) ; sur ordinateur,
    le texte + le lien sont copiés. Code dans assets/page.js (écouteur sur button[data-partage-rapport], CSP : rien en ligne)."""
    E = C.E
    # AUCUNE adresse dans le texte (18/10/2026, vu par Ahmed) : Facebook prendrait la 1re adresse du texte (l'accueil) au lieu du rapport
    texte = f"{titre} — Rapport du mois d’{NOM_SITE} :"
    texte_ar = f"{titre} — تقرير الشهر من {NOM_SITE_AR}:"
    return (f'<div class="rap-partage{" rap-partage-haut" if haut else ""}">'
            f'<button class="rap-partager" type="button" data-partage-rapport data-url="{C.URL_SITE}{chemin}" data-titre="{E(titre)}" data-texte="{E(texte)}" data-texte-ar="{E(texte_ar)}">'
            '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/></svg>'
            f'<span>{C.L("Partager ce rapport", "شارك هذا التقرير")}</span></button>'
            '<p class="rap-partage-ok" role="status" aria-live="polite"></p></div>')


def page_mois(C, hist, mois, v, maj):
    e = hist["mois"][mois]
    k, au, fini = e["chiffres"], e["dernier_jour"], e.get("fini")
    L, ISO, E, dfr = C.L, C.ISO, C.E, C.dfr
    mfr, mar = nom_mois(mois), nom_mois(mois, True)
    prec = [m for m in hist["mois"] if m < mois]
    prec = prec[-1] if prec else None
    o, nat, loc, sem, nv, cl = k["ouverts"], k["national"], k["locaux"], k["semaine"], k["nouveaux"], k["clos"]
    titre = f"Concours publics en Tunisie, {mfr} : {o['n']} concours ouverts, {_nb(o['postes'])} postes"
    chemin = f"rapports/{mois}/"

    # --- en bref
    bref = [L(f"Au {dfr(au)}, <b id=\"rap-ouverts\">{o['n']}</b> concours publics sont ouverts aux candidatures, pour <b id=\"rap-postes\">{_nb(o['postes'])}</b> postes en tout"
              + (f" ({o['sans_postes']} sans nombre de postes indiqué)" if o["sans_postes"] else "") + ".",
              f"في {ISO(dfr(au))}، <b>{ISO(o['n'])}</b> مناظرة عمومية مفتوحة للترشح، لـ<b>{ISO(_nb(o['postes']))}</b> خطة في المجموع"
              + (f" ({ISO(o['sans_postes'])} دون ذكر عدد الخطط)" if o["sans_postes"] else "") + "."),
            L(f"<b id=\"rap-nationaux\">{nat['n']}</b> concours nationaux (ouverts à toute la Tunisie, {_postes(nat['postes'])}) et <b id=\"rap-locaux\">{loc['n']}</b> concours d'organismes locaux ({_postes(loc['postes'])}) dans {len(k['gouvernorats'])} gouvernorat{'s' if len(k['gouvernorats']) > 1 else ''}.",
              f"<b>{ISO(nat['n'])}</b> مناظرة وطنية (مفتوحة لكل الجمهورية، {_postes(nat['postes'], True, C)}) و<b>{ISO(loc['n'])}</b> مناظرة لهياكل محلية ({_postes(loc['postes'], True, C)}) في {ISO(len(k['gouvernorats']))} ولاية."),
            L(f"<b id=\"rap-semaine\">{sem['n']}</b> concours ferment leurs inscriptions entre le {dfr(au)} et le {dfr(sem['jusqu_au'])} ({_postes(sem['postes'])}).",
              f"<b>{ISO(sem['n'])}</b> مناظرة ينتهي أجل الترشح فيها بين {ISO(dfr(au))} و{ISO(dfr(sem['jusqu_au']))} ({_postes(sem['postes'], True, C)}).")]
    if len(k["metiers"]) >= MIN_LIGNES:
        m0 = C.M_PAR[k["metiers"][0][0]]
        bref.append(L(f"Métier le plus représenté : <b>{E(m0[1])}</b> ({k['metiers'][0][1]} concours ouverts sur {o['n']}).",
                      f"الاختصاص الأكثر حضورًا: <b>{m0[2]}</b> ({ISO(k['metiers'][0][1])} مناظرة مفتوحة من {ISO(o['n'])})."))
    if len(k["gouvernorats"]) >= MIN_LIGNES:
        g0 = C.G_PAR[k["gouvernorats"][0][0]]
        bref.append(L(f"Gouvernorat qui compte le plus de concours locaux : <b>{E(g0[1])}</b> ({k['gouvernorats'][0][1]} concours).",
                      f"الولاية التي تضم أكثر المناظرات المحلية: <b>{g0[2]}</b> ({ISO(k['gouvernorats'][0][1])} مناظرة)."))
    bref.append(L(f"Du {dfr(k['debut'])} au {dfr(au)} : <b id=\"rap-nouveaux\">{nv['n']}</b> nouveaux concours ouverts apparus dans le tableau officiel ({_postes(nv['postes'])}).",
                  f"من {ISO(dfr(k['debut']))} إلى {ISO(dfr(au))}: <b>{ISO(nv['n'])}</b> مناظرة مفتوحة جديدة ظهرت في الجدول الرسمي ({_postes(nv['postes'], True, C)})."))
    bref.append(L(f"Du {dfr(mois + '-01')} au {dfr(au)} : <b id=\"rap-avis\">{k['avis']['n']}</b> avis publiés sur le portail officiel (résultats, convocations, nouveaux concours…).",
                  f"من {ISO(dfr(mois + '-01'))} إلى {ISO(dfr(au))}: <b>{ISO(k['avis']['n'])}</b> بلاغًا منشورًا في البوابة الرسمية (نتائج، استدعاءات، مناظرات جديدة…)."))
    sections = [f'<section class="carte" id="en-bref"><h2>{L("En bref", "باختصار")}</h2><ul class="rap-bref">' + "".join(f"<li>{x}</li>" for x in bref) + "</ul></section>"]

    # --- évolution (seulement si le mois précédent existe dans l'historique)
    if prec:
        p = hist["mois"][prec]
        pk, pau = p["chiffres"], p["dernier_jour"]
        ev = lambda a, b: ("=" if a == b else f"{'+' if a > b else '−'}{_nb(abs(a - b))}")
        lignes = []
        for fr, ar, cle, sous in [("Concours ouverts", "المناظرات المفتوحة", "ouverts", "n"), ("Postes des concours ouverts", "خطط المناظرات المفتوحة", "ouverts", "postes"),
                                  ("Concours nationaux ouverts", "المناظرات الوطنية المفتوحة", "national", "n"), ("Concours locaux ouverts", "المناظرات المحلية المفتوحة", "locaux", "n")]:
            a, b = k[cle][sous], pk[cle][sous]
            lignes.append(f'<tr data-cle="{cle}-{sous}"><th scope="row">{L(fr, ar)}</th><td>{ISO(_nb(b))}</td><td>{ISO(_nb(a))}</td><td>{ISO(ev(a, b))}</td></tr>')
        sections.append(f'<section class="carte" id="evolution"><h2>{L(f"Évolution depuis {nom_mois(prec)}", f"التطور منذ {nom_mois(prec, True)}")}</h2>'
                        + _table(C, [("", ""), (f"au {dfr(pau)}", f"في {ISO(dfr(pau))}"), (f"au {dfr(au)}", f"في {ISO(dfr(au))}"), ("Écart", "الفرق")], lignes)
                        + f'<p class="note">{L("Même mesure aux deux dates : concours ouverts aux candidatures ce jour-là dans le tableau officiel.", "نفس القياس في التاريخين: المناظرات المفتوحة للترشح في ذلك اليوم في الجدول الرسمي.")}</p></section>')
    else:
        sections.append(f'<section class="carte" id="premier-rapport"><p>{L("Premier rapport : pas encore de mois précédent à comparer. L’évolution apparaîtra dans le rapport du mois prochain.", "أول تقرير: لا يوجد بعد شهر سابق للمقارنة. سيظهر التطور في تقرير الشهر القادم.")}</p></section>')

    # --- par métier
    lm = [f'<tr data-metier="{m}" data-n="{n}" data-postes="{p_}"><th scope="row"><a href="../../metier/{m}/">{L(E(C.M_PAR[m][1]), C.M_PAR[m][2])}</a></th><td>{ISO(n)}</td><td>{ISO(_nb(p_))}</td></tr>'
          for m, n, p_ in k["metiers"]]
    sections.append(f'<section class="carte" id="metiers"><h2>{L("Concours ouverts par métier", "المناظرات المفتوحة حسب الاختصاص")}</h2>'
                    + _table(C, [("Métier", "الاختصاص"), ("Concours", "مناظرات"), ("Postes", "خطط")], lm)
                    + f'<p class="note">{L("Métier déduit du grade écrit dans le tableau officiel (ex. « مهندس » = ingénieurs).", "الاختصاص مستنتج من الخطة المكتوبة في الجدول الرسمي.")}</p></section>')

    # --- par gouvernorat
    lg = [f'<tr data-gouv="{g}" data-n="{n}" data-postes="{p_}"><th scope="row"><a href="../../gouvernorat/{g}/">{L(E(C.G_PAR[g][1]), C.G_PAR[g][2])}</a></th><td>{ISO(n)}</td><td>{ISO(_nb(p_))}</td></tr>'
          for g, n, p_ in k["gouvernorats"]]
    lg.append(f'<tr data-gouv="national" data-n="{nat["n"]}" data-postes="{nat["postes"]}"><th scope="row"><a href="../../gouvernorat/national/">{L("Concours nationaux (toute la Tunisie)", "مناظرات وطنية (كل الجمهورية)")}</a></th><td>{ISO(nat["n"])}</td><td>{ISO(_nb(nat["postes"]))}</td></tr>')
    sans, nn, nnp = 24 - len(k["gouvernorats"]), nat["n"], nat["postes"]
    note_g = L(f"Gouvernorat de l’organisme qui recrute. {sans} gouvernorat(s) sans concours local ouvert ce jour-là ; les {nn} concours nationaux y sont ouverts aussi.",
               f"ولاية الهيكل الذي ينتدب. {ISO(sans)} ولاية دون مناظرة محلية مفتوحة في ذلك اليوم؛ والمناظرات الوطنية الـ{ISO(nn)} مفتوحة فيها أيضًا.")
    sections.append(f'<section class="carte" id="gouvernorats"><h2>{L("Concours ouverts par gouvernorat", "المناظرات المفتوحة حسب الولاية")}</h2>'
                    + _table(C, [("Gouvernorat", "الولاية"), ("Concours locaux", "مناظرات محلية"), ("Postes", "خطط")], lg)
                    + f'<p class="note">{note_g}</p></section>')

    # --- organismes (au moins MIN_ORG concours, au moins MIN_LIGNES organismes)
    if len(k["organismes"]) >= MIN_LIGNES:
        lo = [f'<tr data-n="{n}"><th scope="row" dir="rtl" lang="ar">{E(org)}</th><td>{L(E(C.G_PAR.get(g, C.G.NATIONAL)[1]), C.G_PAR.get(g, C.G.NATIONAL)[2])}</td><td>{ISO(n)}</td><td>{ISO(_nb(p_))}</td></tr>'
              for org, n, p_, g in k["organismes"]]
        sections.append(f'<section class="carte" id="organismes"><h2>{L("Organismes qui recrutent le plus", "الهياكل الأكثر انتدابًا")}</h2>'
                        + _table(C, [("Organisme", "الهيكل"), ("Gouvernorat", "الولاية"), ("Concours", "مناظرات"), ("Postes", "خطط")], lo)
                        + f'<p class="note">{L(f"Seuls les organismes qui ont au moins {MIN_ORG} concours ouverts sont classés.", f"لا تُرتب إلا الهياكل التي لها {ISO(MIN_ORG)} مناظرات مفتوحة على الأقل.")}</p></section>')

    # --- ce mois-ci
    types = "".join(f'<li>{L(C.TYPES_ACTU[t][1], C.TYPES_ACTU[t][2])} : {ISO(n)}</li>' for t, n in sorted(k["avis"]["types"].items(), key=lambda x: (-x[1], x[0])) if t in C.TYPES_ACTU)
    nm = ", ".join(f"{C.M_PAR[m][1].lower()} {n}" for m, n in k["nouveaux_metiers"])
    nm_ar = "، ".join(f"{C.M_PAR[m][2]} {ISO(n)}" for m, n in k["nouveaux_metiers"])
    r = k["resultats"]
    deb, d1, dau = dfr(k["debut"]), dfr(k["debut"][:8] + "01"), dfr(au)
    ri, rf, na = r["initial"], r["final"], k["avis"]["n"]
    dres = dfr(max(mois + "-01", DEBUT_SUIVI))     # le robot ne voit les changements de résultats que depuis sa 1re lecture
    items = [
        L(f"Nouveaux concours ouverts apparus dans le tableau officiel du {deb} au {dau} : <b>{nv['n']}</b> ({_postes(nv['postes'])})" + (f" — {E(nm)}" if nm else "") + ".",
          f"مناظرات مفتوحة جديدة ظهرت في الجدول الرسمي من {ISO(deb)} إلى {ISO(dau)}: <b>{ISO(nv['n'])}</b> ({_postes(nv['postes'], True, C)})" + (f" — {nm_ar}" if nm_ar else "") + "."),
        L(f"Concours dont les inscriptions se sont fermées (date limite du {d1} à la veille du {dau}) : <b id='rap-clos'>{cl['n']}</b> ({_postes(cl['postes'])}).",
          f"مناظرات انتهى أجل الترشح فيها (من {ISO(d1)} إلى يوم قبل {ISO(dau)}): <b>{ISO(cl['n'])}</b> ({_postes(cl['postes'], True, C)})."),
        L(f"Résultats publiés dans le tableau officiel du {dres} au {dau} (changement vu par notre robot) : <b>{ri}</b> liste(s) initiale(s), <b>{rf}</b> liste(s) définitive(s).",
          f"نتائج نُشرت في الجدول الرسمي من {ISO(dres)} إلى {ISO(dau)} (تغيير رصده برنامجنا): <b>{ISO(ri)}</b> قائمة أولية، <b>{ISO(rf)}</b> قائمة نهائية."),
        L(f"Avis publiés sur le portail officiel du {d1} au {dau} (date de l’avis) : <b>{na}</b>.", f"بلاغات منشورة في البوابة الرسمية من {ISO(d1)} إلى {ISO(dau)} (تاريخ البلاغ): <b>{ISO(na)}</b>.")
        + (f"<ul>{types}</ul>" if types else ""),
    ]
    note_suivi = (f'<p class="note">' + L(f"Notre robot lit le tableau officiel depuis le {dfr(DEBUT_SUIVI)} : les concours vus ce premier jour ne sont pas comptés comme nouveaux, ni un concours déjà clos qui réapparaît dans le tableau.",
                                          f"يقرأ برنامجنا الجدول الرسمي منذ {ISO(dfr(DEBUT_SUIVI))}: المناظرات التي ظهرت في اليوم الأول لا تُحتسب جديدة، ولا مناظرة منتهية تعود إلى الجدول.") + "</p>") if k["debut"] > mois + "-01" else ""
    sections.append(f'<section class="carte" id="ce-mois"><h2>' + L(f"Ce qui s’est passé en {mfr}", f"ما حدث في {mar}")
                    + '</h2><ul class="rap-bref">' + "".join(f"<li>{x}</li>" for x in items) + "</ul>" + note_suivi + "</section>")

    # --- aller plus loin, méthode, citer
    sections.append(f'''<section class="carte" id="plus-loin"><h2>{L("Aller plus loin", "للمزيد")}</h2><p class="rap-liens">
<a class="btn" href="../../">{L("Tous les concours ouverts", "كل المناظرات المفتوحة")}</a> <a class="btn" href="../../actualites/">{L("Actualités : résultats, convocations", "الأخبار: النتائج، الاستدعاءات")}</a> <a class="btn" href="../">{L("Tous les rapports du mois", "كل التقارير الشهرية")}</a></p></section>
<section class="carte" id="methode"><h2>{L("Comment ces chiffres sont calculés", "كيف تُحسب هذه الأرقام")}</h2><ul class="rap-bref">
<li>{L("Source : le tableau officiel des concours publics (concours.gov.tn) et la plateforme des concours du ministère des Finances (concours.finances.gov.tn), lus chaque jour par notre robot ; les avis viennent du portail officiel.", "المصدر: الجدول الرسمي للمناظرات العمومية (concours.gov.tn) ومنصة مناظرات وزارة المالية (concours.finances.gov.tn)، يقرؤهما برنامجنا كل يوم؛ والبلاغات من البوابة الرسمية.")}</li>
<li>{L("« Ouvert » : la date limite des candidatures n’est pas encore passée ce jour-là (même règle que la liste de l’accueil). Les postes sont ceux écrits dans le tableau officiel.", "« مفتوحة »: لم ينته أجل الترشح في ذلك اليوم (نفس قاعدة قائمة الصفحة الرئيسية). الخطط هي المكتوبة في الجدول الرسمي.")}</li>
<li>{L(f"Un classement n’est montré qu’avec au moins {MIN_LIGNES} éléments ; un organisme n’est classé qu’avec au moins {MIN_ORG} concours ouverts.", f"لا يظهر أي ترتيب إلا بـ{ISO(MIN_LIGNES)} عناصر على الأقل؛ ولا يُرتب الهيكل إلا بـ{ISO(MIN_ORG)} مناظرات مفتوحة على الأقل.")}</li>
<li>{L("Aucune estimation : chaque nombre est un comptage. Le mois en cours est recalculé chaque jour ; un mois terminé n’est plus jamais modifié.", "لا تقديرات: كل رقم هو عدّ. الشهر الجاري يُعاد حسابه كل يوم؛ والشهر المنتهي لا يُغيَّر أبدًا.")}</li>
<li>{L("Site indépendant, non officiel : seul le portail officiel fait foi.", "موقع مستقل وغير رسمي: البوابة الرسمية هي المرجع الوحيد.")}</li></ul></section>
<section class="carte" id="citer"><h2>{L("Citer ces chiffres", "الاستشهاد بهذه الأرقام")}</h2>
<p>{L("Journalistes, blogs, écoles : vous pouvez reprendre ces chiffres en citant la source avec ce lien.", "صحفيون، مدوّنات، مدارس: يمكنكم نقل هذه الأرقام مع ذكر المصدر بهذا الرابط.")}</p>
<p class="rap-citer">Source : Alerte Concours Tunisie, « {E(titre)} », {C.URL_SITE}{chemin}</p></section>''')
    sections.insert(0, bloc_partage(C, titre, chemin, haut=True))
    sections.append(bloc_partage(C, titre, chemin))
    sections.append(C.bouton_alertes("../../"))

    etat = (L(f"Mois terminé : chiffres au {dfr(au)}, figés.", f"شهر منتهٍ: الأرقام في {ISO(dfr(au))}، نهائية.") if fini
            else L(f"Chiffres au {dfr(au)} — mois en cours, mis à jour chaque jour.", f"الأرقام في {ISO(dfr(au))} — الشهر الجاري، تحيين يومي."))
    hero = f"""    <p class="fil"><a href="../../">{L("Accueil", "الرئيسية")}</a> › <a href="../">{L("Rapports du mois", "التقارير الشهرية")}</a> › {L(mfr, mar)}</p>
    <h1>{L(f"Concours publics en Tunisie : le rapport {de(mfr)}", f"المناظرات العمومية في تونس: تقرير {mar}")}</h1>
{signature(C)}
    <p class="intro" id="rap-etat">{etat}</p>"""
    desc = (f"{DESC_DEBUT}{mfr.capitalize()} : {o['n']} concours publics ouverts en Tunisie au {dfr(au)}, {_nb(o['postes'])} postes ; {nat['n']} nationaux, {loc['n']} locaux ; "
            f"par métier, gouvernorat et organisme. Chiffres du tableau officiel. تقرير المناظرات.")
    jsonld = lambda x: '<script type="application/ld+json">\n' + json.dumps(x, ensure_ascii=False) + "\n</script>\n"
    faq = [(f"Combien de concours publics sont ouverts en Tunisie en {mfr} ?",
            f"Au {dfr(au)}, {o['n']} concours publics sont ouverts aux candidatures, pour {_nb(o['postes'])} postes : {nat['n']} nationaux et {loc['n']} locaux.")]
    if len(k["gouvernorats"]) >= MIN_LIGNES:
        faq.append((f"Quel gouvernorat a le plus de concours locaux en {mfr} ?",
                    f"{C.G_PAR[k['gouvernorats'][0][0]][1]}, avec {k['gouvernorats'][0][1]} concours ouverts au {dfr(au)}, sans compter les {nat['n']} concours nationaux ouverts à toute la Tunisie."))
    ld = (jsonld({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Accueil", "item": C.URL_SITE},
              {"@type": "ListItem", "position": 2, "name": "Rapports du mois", "item": C.URL_SITE + "rapports/"},
              {"@type": "ListItem", "position": 3, "name": mfr, "item": C.URL_SITE + chemin}]})
          + jsonld({"@context": "https://schema.org", "@type": "Article", "headline": titre, "inLanguage": ["fr", "ar"],
                    "datePublished": e["premier_jour"], "dateModified": au, "url": C.URL_SITE + chemin,
                    "author": {"@type": "Organization", "name": "Alerte Concours Tunisie", "url": C.URL_SITE},
                    "publisher": {"@type": "Organization", "name": "Alerte Concours Tunisie", "url": C.URL_SITE},
                    "image": C.URL_SITE + "assets/og-image-v2.jpg"})
          + jsonld({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
              {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}))
    return C.page(chemin, "../../", titre + " | Alerte Concours Tunisie", desc, hero, "\n".join(sections), v, maj, ld)


def page_liste(C, hist, v, maj):
    L, ISO, dfr = C.L, C.ISO, C.dfr
    items = ""
    for m, e in sorted(hist["mois"].items(), reverse=True):
        k = e["chiffres"]
        items += (f'<li><a href="{m}/">{L(nom_mois(m).capitalize(), nom_mois(m, True))}</a> — '
                  + L(f"{k['ouverts']['n']} concours ouverts, {_nb(k['ouverts']['postes'])} postes (chiffres au {dfr(e['dernier_jour'])}" + (", figés)" if e.get("fini") else ", mois en cours)"),
                      f"{ISO(k['ouverts']['n'])} مناظرة مفتوحة، {ISO(_nb(k['ouverts']['postes']))} خطة (الأرقام في {ISO(dfr(e['dernier_jour']))}" + ("، نهائية)" if e.get("fini") else "، الشهر الجاري)"))
                  + "</li>")
    hero = f"""{C.fil("../", "Rapports du mois", "التقارير الشهرية")}
    <h1>{L("Rapports du mois : les concours publics en chiffres", "التقارير الشهرية: المناظرات العمومية بالأرقام")}</h1>
{signature(C)}
    <p class="intro">{L("Chaque mois, les concours publics ouverts en Tunisie comptés à partir du tableau officiel : par métier, par gouvernorat et par organisme.", "كل شهر، المناظرات العمومية المفتوحة في تونس معدودة من الجدول الرسمي: حسب الاختصاص والولاية والهيكل.")}</p>"""
    tl = "Rapports du mois : les concours publics en Tunisie en chiffres"
    contenu = (bloc_partage(C, tl, "rapports/", haut=True) + f'<section class="carte"><ul class="rap-mois">{items}</ul>'
               f'<p class="note">{L("Le mois en cours est mis à jour chaque jour ; un mois terminé n’est plus jamais modifié. Aucune estimation : chaque nombre est un comptage.", "الشهر الجاري يُحيَّن كل يوم؛ والشهر المنتهي لا يُغيَّر أبدًا. لا تقديرات: كل رقم هو عدّ.")}</p></section>'
               + bloc_partage(C, tl, "rapports/") + C.bouton_alertes("../"))
    return C.page("rapports/", "../", tl + " | Alerte Concours Tunisie",
                  DESC_DEBUT + "Chaque mois, les concours publics ouverts en Tunisie en chiffres : nombre de concours et de postes, par métier, gouvernorat et organisme, d'après le tableau officiel. تقارير المناظرات.",
                  hero, contenu, v, maj)


def pages(C, hist, v, maj):
    """{chemin: html} et {chemin: date des chiffres} (lastmod du plan du site)."""
    if not hist.get("mois"):
        return {}, {}
    out = {"rapports/": page_liste(C, hist, v, maj)}
    dates = {"rapports/": max(e["dernier_jour"] for e in hist["mois"].values())}
    for m, e in hist["mois"].items():
        out[f"rapports/{m}/"] = page_mois(C, hist, m, v, maj)
        dates[f"rapports/{m}/"] = e["dernier_jour"]
    return out, dates


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aujourdhui", help="date des chiffres (par défaut : date de lecture du tableau, « lu_le »)")
    ap.add_argument("--hist", default=HIST)
    a = ap.parse_args()
    d = json.load(open(os.path.join(RACINE, "donnees", "concours.json"), encoding="utf-8"))
    fa = os.path.join(RACINE, "donnees", "actualites.json")
    actus = json.load(open(fa, encoding="utf-8"))["actualites"] if os.path.exists(fa) else []
    jour = a.aujourdhui or d.get("lu_le") or dt.date.today().isoformat()
    hist = mettre_a_jour(charger_hist(a.hist), d["concours"], actus, jour)
    json.dump(hist, open(a.hist, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    e = hist["mois"].get(jour[:7])
    print(f"Rapport {jour[:7]} : " + (f"chiffres au {e['dernier_jour']}, {e['chiffres']['ouverts']['n']} concours ouverts" if e else "rien à changer"))


if __name__ == "__main__":
    main()
