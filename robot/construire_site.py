"""Fabrique les pages d'Alerte Concours Tunisie à partir de donnees/concours.json (robot/lire_concours.py).
  python robot/construire_site.py [--aujourdhui AAAA-MM-JJ]

Pages : accueil (tous les concours ouverts, filtres gouvernorat + métier, compte à rebours), une page par gouvernorat
(24 + « Toute la Tunisie » ; un concours national apparaît dans CHAQUE gouvernorat), une page par métier, guide
« s'inscrire à un concours », alertes (bientôt), à propos et sources ; sitemap, robots.txt, manifeste.
Gabarit, styles et scripts repris d'Alertes appels d'offres Tunisie (même famille de sites)."""
import argparse, datetime as dt, hashlib, html, json, os, sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, ICI)
import gouvernorats as G      # noqa: E402
import lire_concours as R     # noqa: E402

URL_SITE = "https://ah6259.github.io/alerte-concours-tunisie/"
URL_PORTAIL = "https://www.concours.gov.tn/"
COMPTEUR = "https://prix-eaux-tunisie.goatcounter.com"
FORMSPREE = "https://formspree.io"
CSP = ("default-src 'self'; script-src 'self' https://gc.zgo.at; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
       f"font-src 'self' https://fonts.gstatic.com; img-src 'self' data: {COMPTEUR}; connect-src 'self' {COMPTEUR} {FORMSPREE}; "
       f"form-action 'self' {FORMSPREE}; frame-src 'none'; object-src 'none'; base-uri 'self'")
E = lambda t: html.escape(str(t or ""), quote=True)
ISO = lambda t: "⁦" + str(t) + "⁩"
METIERS = [(s, fr, ar) for s, fr, ar, _ in R.METIERS] + [R.AUTRE]
M_PAR = {m[0]: m for m in METIERS}
GOUVS = [(s, fr, ar) for s, fr, ar, _ in G.GOUVERNORATS]
G_PAR = {g[0]: g for g in GOUVS}
G_PAR["national"] = G.NATIONAL
MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def L(fr, ar):
    return f'<span data-l="fr">{fr}</span><span data-l="ar">{ar}</span>'


def dfr(d):
    return f"{d[8:10]}/{d[5:7]}/{d[:4]}" if d else ""


def charger(jour):
    d = json.load(open(os.path.join(RACINE, "donnees", "concours.json"), encoding="utf-8"))
    ouverts = [c for c in d["concours"] if not c.get("cloture_candidatures") or c["cloture_candidatures"] >= jour]
    return d, ouverts


ICONE_LIEU = '<svg viewBox="0 0 24 24"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>'
ICONE_LIEN = '<svg viewBox="0 0 24 24"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>'


def resultat(c):
    # « اطلاع » (consulter) = résultat publié ; « لم تنشر » (pas encore publié) ou « -- » (rien pour l'instant)
    if "اطلاع" in (c.get("resultat_final") or ""):
        return L("résultats définitifs publiés sur le portail", "النتائج النهائية منشورة في البوابة")
    if "اطلاع" in (c.get("resultat_initial") or ""):
        return L("résultats initiaux publiés sur le portail", "النتائج الأولية منشورة في البوابة")
    return L("pas encore publiés", "لم تنشر بعد")


def carte(c, racine, jour):
    m, g = M_PAR[c["metier"]], G_PAR[c["gouvernorat"]]
    lim = c.get("cloture_candidatures") or ""
    reste = (dt.date.fromisoformat(lim) - dt.date.fromisoformat(jour)).days if lim else None
    urgent = reste is not None and 0 <= reste < 7
    reste_fr = "voir le portail" if reste is None else "aujourd'hui !" if reste == 0 else "demain !" if reste == 1 else f"dans {reste} jours"
    postes = c.get("postes")
    p_fr = f"{postes} poste{'s' if postes and postes > 1 else ''}" if postes else "voir le portail"
    p_ar = f"{ISO(postes)} {'خطة' if postes == 1 else 'خطط'}" if postes else "انظر البوابة"
    gouv_lien = f'{racine}gouvernorat/{g[0]}/'
    return f"""<article class="ao{' urgent' if urgent else ''}" id="c-{E(c['id'])}" data-num="{E(c['id'])}" data-metier="{m[0]}" data-gouv="{g[0]}" data-limite="{lim}" data-pub="{E(c.get('vu_le', ''))}">
 <div class="ao-haut"><a class="pastille" href="{racine}metier/{m[0]}/">{L(E(m[1]), m[2])}</a><a class="pastille gouv" href="{gouv_lien}">{ICONE_LIEU}{L(E(g[1]), g[2])}</a><span class="nouveau" hidden>{L("Nouveau", "جديد")}</span><span class="rappel" hidden></span></div>
 <h3 dir="rtl" lang="ar"><a href="{racine}concours/{E(c['id'])}/">{E(c['grade'])}</a></h3>
 <p class="acheteur" dir="rtl" lang="ar">{E(c['organisme'])}</p>
 <div class="ao-infos">
  <div class="limite"><span>{L("Inscription jusqu'au", "آخر أجل للترشح")}</span><b>{L(dfr(lim) or "non indiquée", ISO(dfr(lim)) if lim else "غير مذكور")}</b><small class="reste">{reste_fr}</small></div>
  <div><span>{L("Postes", "عدد الخطط")}</span><b>{L(p_fr, p_ar)}</b></div>
 </div>
 <p class="ao-type">{L(f"Concours n° {E(c['id'])} · résultats : ", f"المناظرة عدد {ISO(E(c['id']))} · النتائج: ")}{resultat(c)}</p>
 <a class="officiel" href="{URL_PORTAIL}P1/index5.aspx?id=5" target="_blank" rel="noopener">{L("S'inscrire sur le portail officiel <small>(concours.gov.tn)</small>", "الترشح في البوابة الرسمية <small>(concours.gov.tn)</small>")}{ICONE_LIEN}</a>
</article>"""


def options(items, tous_fr, tous_ar, compte, total):
    o = [f'<option value="" data-fr="{tous_fr}" data-ar="{tous_ar}">{tous_fr} ({total})</option>']
    for s, fr, ar in items:
        o.append(f'<option value="{s}" data-fr="{E(fr)}" data-ar="{ar}">{E(fr)} ({compte.get(s, 0)})</option>')
    return "\n".join(o)


def comptes(cs):
    cm, cg = {}, {}
    for c in cs:
        cm[c["metier"]] = cm.get(c["metier"], 0) + 1
        cg[c["gouvernorat"]] = cg.get(c["gouvernorat"], 0) + 1
    nat = cg.get("national", 0)
    cg_vis = {s: cg.get(s, 0) + nat for s, _, _ in GOUVS}     # un concours national compte dans chaque gouvernorat
    cg_vis["national"] = nat
    return cm, cg_vis


def filtres(cs, avec_metier=True, avec_gouv=True):
    cm, cg = comptes(cs)
    blocs = [f'<div class="f-q"><label for="f-q">{L("Rechercher", "بحث")}</label>'
             '<input id="f-q" type="search" enterkeyhint="search" autocomplete="off" placeholder="Grade, organisme, ville…" '
             'data-fr="Grade, organisme, ville…" data-ar="الخطة، الهيكل، المدينة…"></div>']
    if avec_metier:
        blocs.append(f'<div><label for="f-metier">{L("Métier", "الاختصاص")}</label><select id="f-metier">'
                     f'{options(METIERS, "Tous les métiers", "كل الاختصاصات", cm, len(cs))}</select></div>')
    if avec_gouv:
        blocs.append(f'<div><label for="f-gouv">{L("Gouvernorat", "الولاية")}</label><select id="f-gouv">'
                     f'{options(GOUVS + [G.NATIONAL], "Tous les gouvernorats", "كل الولايات", cg, len(cs))}</select></div>')
    blocs.append(f'<div class="f-tri"><label for="f-tri">{L("Trier par", "الترتيب حسب")}</label><select id="f-tri">'
                 '<option value="limite" data-fr="Date limite la plus proche" data-ar="أقرب آخر أجل">Date limite la plus proche</option>'
                 '<option value="recent" data-fr="Plus récents d\'abord" data-ar="الأحدث أولاً">Plus récents d\'abord</option></select></div>')
    return f'<section class="carte filtres{"" if avec_metier and avec_gouv else " deux"}">{"".join(blocs)}</section>'


def liste_html(cs, racine, jour, vide_fr, vide_ar):
    n = len(cs)
    return f"""<p class="compte" id="compte" aria-live="polite"><span>{n} concours ouvert{'s' if n > 1 else ''}</span></p>
<div class="liste" id="liste">
{chr(10).join(carte(c, racine, jour) for c in cs)}
</div>
<button type="button" class="plus" id="plus" hidden>Afficher plus</button>
<p class="carte vide" id="vide"{' hidden' if cs else ''}>{L(vide_fr, vide_ar)}</p>"""


def grille(items, racine, dossier, compte, ident):
    liens = []
    for s, fr, ar in items:
        n = compte.get(s, 0)
        liens.append(f'<a href="{racine}{dossier}/{s}/"{" class=" + chr(34) + "zero" + chr(34) if not n else ""}><span>{L(E(fr), ar)}</span><span class="n">{n}</span></a>')
    return f'<div class="grille" id="{ident}">{"".join(liens)}</div>'


AVIS = """<section class="carte avis" id="avis" aria-labelledby="avis-titre">
  <h2 id="avis-titre"><span data-l="fr">Votre avis</span><span data-l="ar">رأيك يهمّنا</span></h2>
  <p class="avis-intro"><span data-l="fr">Une remarque, une erreur, une idée ? Écrivez-nous : chaque message est lu.</span><span data-l="ar">ملاحظة، خطأ، فكرة؟ اكتب لنا: كل رسالة تُقرأ.</span></p>
  <form id="avis-form" action="https://formspree.io/f/mwlpakqj" method="POST">
    <fieldset>
      <legend><span data-l="fr">Votre note (facultatif)</span><span data-l="ar">تقييمك (اختياري)</span></legend>
      <div class="avis-notes">
        <label><input type="radio" name="note" value="😀 Très bien"><span class="emoji" aria-hidden="true">😀</span><span class="avis-cache"><span data-l="fr">Très bien</span><span data-l="ar">ممتاز</span></span></label>
        <label><input type="radio" name="note" value="🙂 Bien"><span class="emoji" aria-hidden="true">🙂</span><span class="avis-cache"><span data-l="fr">Bien</span><span data-l="ar">جيد</span></span></label>
        <label><input type="radio" name="note" value="😐 Moyen"><span class="emoji" aria-hidden="true">😐</span><span class="avis-cache"><span data-l="fr">Moyen</span><span data-l="ar">متوسط</span></span></label>
        <label><input type="radio" name="note" value="🙁 Pas bien"><span class="emoji" aria-hidden="true">🙁</span><span class="avis-cache"><span data-l="fr">Pas bien</span><span data-l="ar">سيئ</span></span></label>
      </div>
    </fieldset>
    <label class="avis-etiquette" for="avis-message"><span data-l="fr">Votre message</span><span data-l="ar">رسالتك</span></label>
    <textarea id="avis-message" name="message" required maxlength="1000" rows="4" data-ph-fr="Ce qui vous plaît, ce qui manque, une erreur à corriger…" data-ph-ar="ما يعجبك، ما ينقص، خطأ يجب تصحيحه…"></textarea>
    <span class="avis-compte" id="avis-compte" aria-live="off">0 / 1000</span>
    <label class="avis-etiquette" for="avis-email"><span data-l="fr">Votre e-mail (facultatif, pour vous répondre)</span><span data-l="ar">بريدك الإلكتروني (اختياري، للرد عليك)</span></label>
    <input type="email" id="avis-email" name="email" autocomplete="email" maxlength="200" data-ph-fr="nom@example.com" data-ph-ar="nom@example.com">
    <input type="hidden" name="site" value="Alerte Concours Tunisie">
    <input type="hidden" name="page" value="">
    <input type="hidden" name="_subject" value="Avis — Alerte Concours Tunisie">
    <input type="text" name="_gotcha" class="avis-piege" tabindex="-1" autocomplete="off" aria-hidden="true">
    <div class="avis-actions">
      <button type="submit" class="avis-envoyer"><span data-l="fr">Envoyer</span><span data-l="ar">إرسال</span></button>
      <span id="avis-status" role="status" aria-live="polite"></span>
    </div>
    <p class="avis-mention"><span data-l="fr">Votre avis est envoyé au créateur du site (service Formspree). Rien n&#39;est envoyé sans clic sur « Envoyer ».</span><span data-l="ar">يُرسل رأيك إلى صاحب الموقع (خدمة ⁨Formspree⁩). لا يُرسل أي شيء دون الضغط على «إرسال».</span></p>
  </form>
</section>"""


def page(chemin, racine, titre, description, hero, contenu, v, maj, jsonld=""):
    canon = URL_SITE + chemin
    return f"""<!doctype html>
<html lang="fr" dir="ltr" translate="no" data-racine="{racine}">
<head>
<meta charset="utf-8">
<meta name="google" content="notranslate">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{CSP}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="robots" content="noai, noimageai">
<title>{E(titre)}</title>
<meta name="description" content="{E(description)}">
<link rel="canonical" href="{canon}">
<link rel="icon" href="{racine}assets/logo.svg" type="image/svg+xml">
<link rel="icon" href="{racine}favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="{racine}assets/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Alerte Concours">
<link rel="manifest" href="{racine}manifest.webmanifest">
<meta name="theme-color" content="#1F6B60">
<meta property="og:title" content="{E(titre.split(' | ')[0])}">
<meta property="og:description" content="{E(description)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{URL_SITE}assets/og-image-v1.png">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_TN"><meta property="og:locale:alternate" content="ar_TN">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;600;700;800&family=Noto+Kufi+Arabic:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{racine}assets/style.css?v={v}">
{jsonld}<script src="{racine}assets/page.js?v={v}"></script>
<script src="{racine}assets/app.js?v={v}"></script>
<script src="{racine}assets/avis.js?v={v}"></script>
</head>
<body data-maj="{maj}" data-maj-texte="{dfr(maj)}" data-panne="0">
<header class="entete" id="entete"></header>
<section class="hero">
  <div class="wrap">
{hero}
    <span class="maj">{L("Mis à jour le", "تحيين")}&nbsp;{ISO(dfr(maj)) if maj else '—'}</span>
  </div>
</section>
<main class="wrap chevauche">
<div class="alerte-panne" id="alerte-panne" role="status"></div>
{contenu}
</main>
<footer id="pied"><div class="wrap"><p>Source : portail officiel des concours publics (concours.gov.tn) · © 2026 Alerte Concours Tunisie — tous droits réservés.</p></div></footer>
<script data-goatcounter="{COMPTEUR}/count" async src="https://gc.zgo.at/count.js"></script>
</body>
</html>
"""


def fil(racine, fr, ar):
    return f'    <p class="fil"><a href="{racine}">{L("Accueil", "الرئيسية")}</a> › {L(fr, ar)}</p>'


def bouton_alertes(racine):
    return (f'<section class="carte alertes-appel"><h2>{L("🔔 Recevez les nouveaux concours de VOTRE métier et de VOTRE gouvernorat", "🔔 استقبل المناظرات الجديدة في اختصاصك وولايتك")}</h2>'
            f'<p>{L("Chaque matin sur Telegram, seulement ce qui vous concerne, et le suivi de vos concours (candidatures acceptées, convocations, résultats).", "كل صباح على تيليغرام، فقط ما يهمك، مع متابعة مناظراتك (قبول الترشحات، الاستدعاءات، النتائج).")}</p>'
            f'<a class="btn" href="{racine}alertes/">{L("Découvrir les alertes", "اكتشف التنبيهات")}</a></section>')


GUIDE = [
    ("Créer votre compte", "أنشئ حسابك",
     "Sur www.concours.gov.tn, choisissez « Nouvelle inscription » dans l'espace « Demandeur d'emploi ». Votre identifiant est le numéro de votre carte d'identité nationale (8 chiffres) ; choisissez un mot de passe.",
     "في موقع www.concours.gov.tn، اختر « تسجيل جديد » في « فضاء طالب شغل ». المعرّف هو رقم بطاقة التعريف الوطنية (8 أرقام)، ثم اختر كلمة عبور."),
    ("Compléter votre profil", "أكمل معطياتك",
     "Après la première connexion, remplissez vos informations (diplômes, spécialité, coordonnées) et enregistrez.",
     "بعد أول دخول، عمّر معطياتك (الشهائد، الاختصاص، وسائل الاتصال) ثم سجّلها."),
    ("Trouver le concours", "ابحث عن المناظرة",
     "Cherchez par organisme, nom du concours ou spécialité. Lisez les détails : conditions, pièces demandées et dates. Vous pouvez imprimer les détails.",
     "ابحث حسب الوزارة أو الهيكل أو اسم المناظرة أو الاختصاص. اطّلع على التفاصيل: الشروط والوثائق المطلوبة والآجال. يمكنك طباعة التفاصيل."),
    ("Déposer votre candidature", "قدّم ترشحك",
     "Choisissez « Postuler », vérifiez puis confirmez. Imprimez et gardez votre demande de candidature : vous pouvez la réimprimer plus tard. Certains organismes demandent aussi une inscription sur leur propre site : suivez toujours l'avis officiel.",
     "اختر « الترشح »، تثبّت ثم أكّد. اطبع مطلب الترشح واحتفظ به، ويمكنك إعادة طباعته لاحقًا. بعض الهياكل تطلب أيضًا تسجيلًا في موقعها الخاص: اتبع دائمًا البلاغ الرسمي."),
    ("Suivre les résultats", "تابع النتائج",
     "Les résultats (liste initiale puis définitive) sont publiés sur le portail, dans la ligne du concours.",
     "تُنشر النتائج (القائمة الأولية ثم النهائية) في البوابة، في سطر المناظرة."),
]


def ecrire(chemin, contenu):
    f = os.path.join(RACINE, chemin, "index.html") if not chemin.endswith(".html") else os.path.join(RACINE, chemin)
    os.makedirs(os.path.dirname(f), exist_ok=True)
    open(f, "w", encoding="utf-8", newline="\n").write(contenu)


def construire(jour):
    d, ouverts = charger(jour)
    maj = d.get("lu_le", "")
    v = hashlib.sha1("".join(open(os.path.join(RACINE, "assets", f), "rb").read().decode("utf-8", "ignore") for f in ("style.css", "page.js", "app.js", "avis.js")).encode()).hexdigest()[:8]
    cm, cg = comptes(ouverts)
    urgents = sum(1 for c in ouverts if c.get("cloture_candidatures") and 0 <= (dt.date.fromisoformat(c["cloture_candidatures"]) - dt.date.fromisoformat(jour)).days < 7)
    postes = sum(c.get("postes") or 0 for c in ouverts)
    pages = {}

    # --- accueil
    hero = f"""    <h1>{L("Tous les concours publics ouverts en Tunisie", "كل المناظرات العمومية المفتوحة في تونس")}</h1>
    <p class="intro">{L(f"Dans les 24 gouvernorats, par gouvernorat et par métier : date limite, nombre de postes et lien officiel pour s'inscrire. Mis à jour chaque jour depuis le portail officiel. Gratuit.",
                         f"في الولايات الـ{ISO(24)}، حسب الولاية والاختصاص: آخر أجل، عدد الخطط والرابط الرسمي للترشح. تحيين يومي من البوابة الرسمية. مجانًا.")}</p>"""
    faq = [("Où s'inscrire à un concours public en Tunisie ?", "Sur le portail officiel des concours publics, www.concours.gov.tn (identifiant : numéro de carte d'identité). Certains organismes demandent aussi une inscription sur leur propre site."),
           ("Les concours sont-ils classés par gouvernorat ?", "Oui. Chaque concours est classé dans le gouvernorat de l'organisme ; un concours national (ministère, office national) est ouvert à toute la Tunisie et apparaît dans chaque gouvernorat."),
           ("Ce site est-il officiel ?", "Non. C'est un site indépendant et gratuit qui reprend chaque jour la liste officielle ; seul le portail officiel fait foi.")]
    jsonld = ('<script type="application/ld+json">\n' + json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}} for q, r in faq]}, ensure_ascii=False) + "\n</script>\n")
    contenu = f"""<section class="carte resume" aria-label="Résumé">
  <div class="r-nouveaux" id="r-nouveaux"><b>0</b><span>{L("nouveaux", "جديدة")}</span></div>
  <div class="r-ouverts" id="r-ouverts"><b>{len(ouverts)}</b><span>{L("concours ouverts", "مناظرة مفتوحة")}</span></div>
  <div class="r-urgent" id="r-urgent"><b>{urgents}</b><span>{L("clôturent sous 7 jours", "تنتهي خلال 7 أيام")}</span></div>
</section>
<p class="postes-total">{L(f"{postes} postes à pourvoir en tout", f"{ISO(postes)} خطة للانتداب في المجموع")}</p>
<section class="carte bientot" id="bientot" hidden aria-labelledby="bientot-titre">
  <h2 id="bientot-titre">{L("⏰ Inscriptions qui se terminent bientôt", "⏰ ترشحات تنتهي قريبًا")}</h2>
  <ol class="bientot-liste" id="bientot-liste"></ol>
</section>
{bouton_alertes("")}
{filtres(ouverts)}
{liste_html(ouverts, "", jour, "Aucun concours ouvert pour ce choix. Essayez un autre métier ou tous les gouvernorats.", "لا توجد مناظرة مفتوحة لهذا الاختيار. جرّب اختصاصًا آخر أو كل الولايات.")}
<h2 class="titre-section" id="gouvernorats">{L("Par gouvernorat", "حسب الولاية")}</h2>
<section class="carte">{grille(GOUVS + [G.NATIONAL], "", "gouvernorat", cg, "grille-gouv")}
<p class="note">{L("Les concours nationaux (ministères, offices nationaux) sont ouverts à toute la Tunisie : ils sont comptés dans chaque gouvernorat.", "المناظرات الوطنية (الوزارات والدواوين الوطنية) مفتوحة لكل الجمهورية: تُحتسب في كل ولاية.")}</p></section>
<h2 class="titre-section" id="metiers">{L("Par métier", "حسب الاختصاص")}</h2>
<section class="carte">{grille(METIERS, "", "metier", cm, "grille-metiers")}</section>
<section class="carte"><h2>{L("Comment s'inscrire ?", "كيف تترشح؟")}</h2><p>{L("L'inscription se fait toujours sur le portail officiel. Notre guide explique les étapes une par une.", "الترشح يتم دائمًا في البوابة الرسمية. دليلنا يشرح المراحل واحدة بواحدة.")}</p>
<a class="btn" href="guide-inscription/">{L("Lire le guide d'inscription", "اقرأ دليل الترشح")}</a></section>
{AVIS}"""
    pages[""] = page("", "", "Concours Tunisie 2026 : tous les concours ouverts par gouvernorat | Alerte Concours Tunisie",
                     f"{len(ouverts)} concours publics ouverts en Tunisie, dans les 24 gouvernorats : date limite, postes, lien officiel. Mis à jour chaque jour. مناظرات تونس.",
                     hero, contenu, v, maj, jsonld)

    # --- gouvernorats (24 + national)
    for s, fr, ar in GOUVS + [G.NATIONAL]:
        cs = [c for c in ouverts if c["gouvernorat"] == s or (s != "national" and c["gouvernorat"] == "national")]
        locaux = sum(1 for c in cs if c["gouvernorat"] == s)
        titre_fr = f"Concours à {fr}" if s != "national" else "Concours nationaux (toute la Tunisie)"
        titre_ar = f"المناظرات في ولاية {ar}" if s != "national" else "المناظرات الوطنية (كل الجمهورية)"
        hero = f"""{fil("../../", fr, ar)}
    <h1>{L(titre_fr, titre_ar)}</h1>
    <p class="intro">{L(f"{locaux} concours d'organismes de ce gouvernorat" + (f" + {len(cs) - locaux} concours nationaux ouverts à toute la Tunisie." if s != "national" else "."),
                         f"{ISO(locaux)} مناظرة لهياكل هذه الولاية" + (f" + {ISO(len(cs) - locaux)} مناظرة وطنية مفتوحة لكل الجمهورية." if s != "national" else "."))}</p>"""
        contenu = f"""{bouton_alertes("../../")}
{filtres(cs, avec_gouv=False)}
{liste_html(cs, "../../", jour, "Aucun concours ouvert pour ce gouvernorat aujourd'hui.", "لا توجد مناظرة مفتوحة في هذه الولاية اليوم.")}
<h2 class="titre-section">{L("Autres gouvernorats", "ولايات أخرى")}</h2>
<section class="carte">{grille([x for x in GOUVS + [G.NATIONAL] if x[0] != s], "../../", "gouvernorat", cg, "grille-gouv")}</section>"""
        pages[f"gouvernorat/{s}/"] = page(f"gouvernorat/{s}/", "../../", f"{titre_fr} 2026 : {len(cs)} concours ouverts | Alerte Concours Tunisie",
                                          f"{titre_fr} : {len(cs)} concours ouverts, date limite, postes et lien officiel. {titre_ar}.", hero, contenu, v, maj)

    # --- métiers
    for s, fr, ar in METIERS:
        cs = [c for c in ouverts if c["metier"] == s]
        hero = f"""{fil("../../", fr, ar)}
    <h1>{L(f"Concours : {fr}", f"مناظرات: {ar}")}</h1>
    <p class="intro">{L(f"{len(cs)} concours ouverts dans toute la Tunisie. Filtrez par gouvernorat.", f"{ISO(len(cs))} مناظرة مفتوحة في كل الجمهورية. اختر الولاية.")}</p>"""
        contenu = f"""{bouton_alertes("../../")}
{filtres(cs, avec_metier=False)}
{liste_html(cs, "../../", jour, "Aucun concours ouvert pour ce métier aujourd'hui.", "لا توجد مناظرة مفتوحة في هذا الاختصاص اليوم.")}
<h2 class="titre-section">{L("Autres métiers", "اختصاصات أخرى")}</h2>
<section class="carte">{grille([x for x in METIERS if x[0] != s], "../../", "metier", cm, "grille-metiers")}</section>"""
        pages[f"metier/{s}/"] = page(f"metier/{s}/", "../../", f"Concours {fr} Tunisie 2026 : {len(cs)} ouverts | Alerte Concours Tunisie",
                                     f"Concours {fr.lower()} en Tunisie : {len(cs)} ouverts, par gouvernorat, date limite et lien officiel. مناظرات {ar}.", hero, contenu, v, maj)

    # --- une page par concours (08/10/2026, plan Google « une page par recherche ») : tous les concours du tableau officiel,
    # ouverts ou clos (les résultats arrivent après la clôture) ; aucune page vide, toujours le lien officiel.
    tous = d["concours"]
    for c in tous:
        m, g = M_PAR[c["metier"]], G_PAR[c["gouvernorat"]]
        lim, fin = c.get("cloture_candidatures") or "", c.get("cloture_concours") or ""
        ouvert = not lim or lim >= jour
        postes = c.get("postes")
        p_fr = f"{postes} poste{'s' if postes and postes > 1 else ''}" if postes else ""
        if ouvert:
            reste = (dt.date.fromisoformat(lim) - dt.date.fromisoformat(jour)).days if lim else None
            etat = L(f"Inscriptions ouvertes jusqu'au {dfr(lim)}" + (f" ({'aujourd’hui' if reste == 0 else 'demain' if reste == 1 else f'encore {reste} jours'})" if reste is not None else "") if lim else "Inscriptions ouvertes",
                     f"الترشح مفتوح إلى غاية {ISO(dfr(lim))}" if lim else "الترشح مفتوح")
        else:
            etat = L(f"Inscriptions closes depuis le {dfr(lim)}", f"انتهى أجل الترشح في {ISO(dfr(lim))}")
        lignes = [("N° du concours", "عدد المناظرة", ISO(E(c["id"]))), ("Décision", "القرار", f'<span dir="rtl" lang="ar">{E(c.get("decision"))}</span>'),
                  ("Organisme", "الهيكل", f'<span dir="rtl" lang="ar">{E(c["organisme"])}</span>'),
                  ("Grade", "الخطة", f'<span dir="rtl" lang="ar">{E(c["grade"])}</span>'),
                  ("Postes", "عدد الخطط", L(p_fr or "voir le portail", ISO(postes) if postes else "انظر البوابة")),
                  ("Clôture des candidatures", "آخر أجل للترشح", L(dfr(lim) or "non indiquée", ISO(dfr(lim)) if lim else "غير مذكور")),
                  ("Clôture du concours", "ختم المناظرة", L(dfr(fin) or "non indiquée", ISO(dfr(fin)) if fin else "غير مذكور")),
                  ("Résultats", "النتائج", resultat(c)),
                  ("Gouvernorat", "الولاية", f'<a href="../../gouvernorat/{g[0]}/">{L(E(g[1]), g[2])}</a>'),
                  ("Métier", "الاختصاص", f'<a href="../../metier/{m[0]}/">{L(E(m[1]), m[2])}</a>')]
        table = "".join(f"<tr><th>{L(a, b)}</th><td>{v_}</td></tr>" for a, b, v_ in lignes)
        proches = [x for x in ouverts if x["id"] != c["id"] and (x["metier"] == c["metier"] or x["gouvernorat"] == c["gouvernorat"])][:8]
        autres = "".join(f'<li><a href="../{E(x["id"])}/" dir="rtl" lang="ar">{E(x["grade"])} — {E(x["organisme"])}</a></li>' for x in proches)
        hero = f"""{fil("../../", f"Concours n° {E(c['id'])}", f"المناظرة عدد {ISO(E(c['id']))}")}
    <h1 dir="rtl" lang="ar">{E(c["grade"])}</h1>
    <p class="intro" dir="rtl" lang="ar">{E(c["organisme"])}</p>
    <p class="intro">{etat}</p>"""
        contenu = f"""<section class="carte"><h2>{L("Le concours", "المناظرة")}</h2>
<table class="fiche-concours">{table}</table>
<a class="officiel" href="{URL_PORTAIL}P1/index5.aspx?id=5" target="_blank" rel="noopener">{L("S'inscrire ou voir le détail sur le portail officiel <small>(concours.gov.tn)</small>", "الترشح أو الاطلاع على التفاصيل في البوابة الرسمية <small>(concours.gov.tn)</small>")}{ICONE_LIEN}</a>
<p class="note">{L("Informations reprises du tableau officiel des concours publics. Seul le portail officiel fait foi : lisez toujours l'avis officiel (conditions, pièces, dates).", "معطيات مأخوذة من الجدول الرسمي للمناظرات العمومية. البوابة الرسمية هي المرجع الوحيد: اطّلع دائمًا على البلاغ الرسمي (الشروط، الوثائق، الآجال).")}</p></section>
<section class="carte"><h2>{L("Comment s'inscrire ?", "كيف تترشح؟")}</h2><p>{L("Sur le portail officiel, avec le numéro de votre carte d'identité. Notre guide explique les étapes une par une.", "في البوابة الرسمية، برقم بطاقة التعريف الوطنية. دليلنا يشرح المراحل واحدة بواحدة.")}</p>
<a class="btn" href="../../guide-inscription/">{L("Lire le guide d'inscription", "اقرأ دليل الترشح")}</a></section>
{bouton_alertes("../../")}
{f'<section class="carte"><h2>{L("Autres concours ouverts proches", "مناظرات مفتوحة قريبة")}</h2><ul class="liens-concours">{autres}</ul></section>' if autres else ""}"""
        titre = f"Concours {m[1]} : {c['grade']} — {c['organisme']}" + (f" ({p_fr})" if p_fr else "")
        desc = (f"Concours n° {c['id']} : {c['grade']}, {c['organisme']}" + (f", {p_fr}" if p_fr else "")
                + (f". Inscription jusqu'au {dfr(lim)}" if ouvert and lim else f". Inscriptions closes le {dfr(lim)}" if lim else "")
                + ". Lien officiel, guide d'inscription, état des résultats. مناظرة.")
        fil_ld = ('<script type="application/ld+json">\n' + json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Alerte Concours Tunisie", "item": URL_SITE},
            {"@type": "ListItem", "position": 2, "name": f"Concours {m[1]}", "item": URL_SITE + f"metier/{m[0]}/"},
            {"@type": "ListItem", "position": 3, "name": f"Concours n° {c['id']}", "item": URL_SITE + f"concours/{c['id']}/"}]}, ensure_ascii=False) + "\n</script>\n")
        pages[f"concours/{c['id']}/"] = page(f"concours/{c['id']}/", "../../", titre[:150] + " | Alerte Concours Tunisie", desc, hero, contenu, v, maj, fil_ld)

    # --- guide d'inscription
    etapes = "".join(f'<li><b>{L(E(tf), ta)}</b><p>{L(E(df), da)}</p></li>' for tf, ta, df, da in GUIDE)
    hero = f"""{fil("../", "S'inscrire à un concours", "كيف تترشح لمناظرة")}
    <h1>{L("Comment s'inscrire à un concours public", "كيف تترشح لمناظرة عمومية")}</h1>
    <p class="intro">{L("Les 5 étapes sur le portail officiel des concours publics, d'après le guide officiel du candidat.", "المراحل الخمس في البوابة الرسمية للمناظرات العمومية، حسب الدليل الرسمي للمترشح.")}</p>"""
    contenu = f"""<section class="carte"><ol class="etapes">{etapes}</ol>
<a class="btn" href="{URL_PORTAIL}" target="_blank" rel="noopener">{L("Ouvrir le portail officiel", "افتح البوابة الرسمية")}</a></section>
{bouton_alertes("../")}"""
    pages["guide-inscription/"] = page("guide-inscription/", "../", "S'inscrire à un concours public en Tunisie (concours.gov.tn) : les étapes | Alerte Concours Tunisie",
                                       "Comment s'inscrire à un concours public en Tunisie sur concours.gov.tn : créer son compte, trouver le concours, postuler, suivre les résultats.", hero, contenu, v, maj)

    # --- alertes (bientôt)
    hero = f"""{fil("../", "Alertes", "التنبيهات")}
    <h1>{L("Alertes concours : votre métier, votre gouvernorat", "تنبيهات المناظرات: اختصاصك وولايتك")}</h1>
    <p class="intro">{L("Bientôt : chaque matin sur Telegram, seulement les nouveaux concours qui vous concernent.", "قريبًا: كل صباح على تيليغرام، فقط المناظرات الجديدة التي تهمك.")}</p>"""
    contenu = f"""<section class="carte"><h2>{L("Ce que vous recevrez", "ما ستتلقاه")}</h2><ul class="avantages">
<li>{L("Les nouveaux concours de votre métier ET de votre gouvernorat (plus les concours nationaux)", "المناظرات الجديدة في اختصاصك وولايتك (مع المناظرات الوطنية)")}</li>
<li>{L("Un rappel avant la date limite d'inscription", "تذكير قبل آخر أجل للترشح")}</li>
<li>{L("Le suivi des concours que vous choisissez : candidatures acceptées, convocations, résultats", "متابعة المناظرات التي تختارها: قبول الترشحات، الاستدعاءات، النتائج")}</li></ul>
<p class="prix">{L("15 DT pour 3 mois · 39 DT pour 1 an", "15 د لـ3 أشهر · 39 د للسنة")}</p>
<p>{L("Ouverture prochaine. En attendant, la liste complète reste gratuite sur ce site, mise à jour chaque jour.", "قريبًا. في الأثناء، القائمة الكاملة تبقى مجانية في هذا الموقع مع تحيين يومي.")}</p></section>
{AVIS}"""
    pages["alertes/"] = page("alertes/", "../", "Alertes concours Tunisie par métier et gouvernorat | Alerte Concours Tunisie",
                             "Bientôt : les nouveaux concours de votre métier et de votre gouvernorat chaque matin sur Telegram, et le suivi de vos concours.", hero, contenu, v, maj)

    # --- à propos
    hero = f"""{fil("../", "À propos et sources", "من نحن والمصادر")}
    <h1>{L("À propos et sources", "من نحن والمصادر")}</h1>"""
    contenu = f"""<section class="carte"><h2>{L("D'où viennent les concours ?", "من أين تأتي المناظرات؟")}</h2>
<p>{L("Chaque jour, un robot lit le tableau officiel des concours ouverts du portail des concours publics (www.concours.gov.tn) : organisme, grade, nombre de postes, dates et état des résultats. Le gouvernorat est déduit du nom de l'organisme ; un concours national est ouvert à toute la Tunisie.",
       "كل يوم، يقرأ برنامج آلي الجدول الرسمي للمناظرات المفتوحة في بوابة المناظرات العمومية (www.concours.gov.tn): الهيكل، الخطة، عدد الخطط، الآجال وحالة النتائج. تُستنتج الولاية من اسم الهيكل؛ والمناظرة الوطنية مفتوحة لكل الجمهورية.")}</p>
<p>{L("Ce site est indépendant et non officiel. Seul le portail officiel fait foi, et l'inscription se fait toujours sur le site officiel.", "هذا الموقع مستقل وغير رسمي. البوابة الرسمية هي المرجع الوحيد، والترشح يتم دائمًا في الموقع الرسمي.")}</p></section>
{AVIS}"""
    pages["a-propos/"] = page("a-propos/", "../", "À propos et sources | Alerte Concours Tunisie", "D'où viennent les concours d'Alerte Concours Tunisie : le portail officiel des concours publics.", hero, contenu, v, maj)

    for chemin, h in pages.items():
        ecrire(chemin, h)
    open(os.path.join(RACINE, "sitemap.xml"), "w", encoding="utf-8", newline="\n").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{URL_SITE}{c}</loc><lastmod>{maj or jour}</lastmod></url>\n" for c in pages) + "</urlset>\n")
    open(os.path.join(RACINE, "robots.txt"), "w", encoding="utf-8", newline="\n").write(
        "User-agent: Googlebot\nAllow: /\n\nUser-agent: Bingbot\nAllow: /\n\n"
        + "".join(f"User-agent: {b}\nDisallow: /\n\n" for b in ("GPTBot", "ChatGPT-User", "OAI-SearchBot", "CCBot", "ClaudeBot", "anthropic-ai", "Google-Extended", "PerplexityBot", "Bytespider", "Amazonbot", "Applebot-Extended", "meta-externalagent", "Diffbot", "omgili", "cohere-ai"))
        + f"User-agent: *\nAllow: /\n\nSitemap: {URL_SITE}sitemap.xml\n")
    json.dump({"id": "/alerte-concours-tunisie/", "name": "Alerte Concours Tunisie", "short_name": "Alerte Concours",
               "description": "Tous les concours publics ouverts en Tunisie, par gouvernorat et par métier.", "start_url": "./", "scope": "./",
               "display": "standalone", "lang": "fr", "dir": "auto", "theme_color": "#1F6B60", "background_color": "#F3F6F9",
               "icons": [{"src": "assets/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
                         {"src": "assets/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
                         {"src": "assets/icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]},
              open(os.path.join(RACINE, "manifest.webmanifest"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"{len(pages)} pages, {len(ouverts)} concours ouverts, version {v}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--aujourdhui", default=dt.date.today().isoformat())
    construire(ap.parse_args().aujourdhui)
