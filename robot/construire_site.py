"""Fabrique les pages d'Alerte Concours Tunisie à partir de donnees/concours.json (robot/lire_concours.py).
  python robot/construire_site.py [--aujourdhui AAAA-MM-JJ]

Pages : accueil (tous les concours ouverts, filtres gouvernorat + métier, compte à rebours), une page par gouvernorat
(24 + « Toute la Tunisie » ; un concours national apparaît dans CHAQUE gouvernorat), une page par métier, guide
« s'inscrire à un concours », alertes (abonnement Telegram) et leurs conditions, à propos et sources ; sitemap, robots.txt, manifeste.
Gabarit, styles et scripts repris d'Alertes appels d'offres Tunisie (même famille de sites)."""
import argparse, datetime as dt, hashlib, html, json, os, sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, ICI)
import gouvernorats as G      # noqa: E402
import lire_concours as R     # noqa: E402
import lire_actualites as A   # noqa: E402

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


# Carte de la Tunisie (08/10/2026, demande d'Ahmed : « comme pour les autres sites ») — même dessin qu'Alertes appels
# d'offres : contour simplifié (longitude, latitude) et chef-lieu de chaque gouvernorat ; Grand Tunis un peu écarté.
CONTOUR_TN = [(8.62, 36.94), (9.0, 37.12), (9.2, 37.23), (9.6, 37.33), (9.87, 37.34), (10.05, 37.27), (10.25, 37.18),
              (10.17, 37.0), (10.25, 36.83), (10.33, 36.78), (10.5, 36.7), (10.8, 36.9), (11.0, 37.06), (11.1, 36.87),
              (10.95, 36.65), (10.75, 36.45), (10.58, 36.38), (10.5, 36.08), (10.64, 35.83), (10.83, 35.78), (10.88, 35.66),
              (11.07, 35.5), (11.12, 35.23), (10.95, 34.95), (10.77, 34.73), (10.5, 34.52), (10.07, 34.3), (10.1, 33.88),
              (10.45, 33.6), (10.75, 33.62), (11.12, 33.5), (11.25, 33.3), (11.56, 33.17), (11.48, 32.62), (11.0, 32.35),
              (10.7, 31.98), (10.3, 31.6), (10.15, 31.0), (9.55, 30.23), (9.3, 30.9), (9.05, 31.9), (8.35, 32.5),
              (7.85, 33.2), (7.5, 33.8), (7.75, 34.2), (8.25, 34.65), (8.4, 35.2), (8.3, 35.7), (8.4, 36.0), (8.42, 36.45),
              (8.2, 36.55)]
POSITIONS_TN = {
    "bizerte": (9.62, 37.1), "ariana": (10.08, 37.08), "tunis": (10.55, 36.98), "manouba": (9.72, 36.72),
    "ben-arous": (10.2, 36.6), "nabeul": (10.9, 36.62), "zaghouan": (10.0, 36.2), "beja": (9.08, 36.72),
    "jendouba": (8.72, 36.55), "le-kef": (8.75, 36.1), "siliana": (9.37, 35.95), "kairouan": (9.95, 35.62),
    "sousse": (10.42, 35.9), "monastir": (10.88, 35.62), "mahdia": (10.9, 35.22), "kasserine": (8.85, 35.2),
    "sidi-bouzid": (9.5, 35.0), "sfax": (10.45, 34.8), "gafsa": (8.75, 34.42), "tozeur": (8.13, 33.95),
    "kebili": (8.95, 33.55), "gabes": (9.85, 33.85), "medenine": (10.75, 33.3), "tataouine": (10.15, 32.55),
}


def _proj(lon, lat):
    import math
    return round((lon - 7.3) * 62 * math.cos(math.radians(34)), 1), round((37.5 - lat) * 62, 1)


def carte_tunisie(locaux, racine, actif=""):
    """Une bulle par gouvernorat : nombre de concours de SES organismes (les nationaux sont en plus, partout)."""
    dj = _proj(10.9, 33.8)
    contour = "M" + " L".join(f"{x},{y}" for x, y in (_proj(*p) for p in CONTOUR_TN)) + "Z"
    bulles = []
    for slug, fr, ar in GOUVS:
        x, y = _proj(*POSITIONS_TN[slug])
        n = locaux.get(slug, 0)
        r = round(min(18, 7.5 + 2.2 * n ** 0.5), 1) if n else 4.5
        if slug == actif:
            r = max(r, 11)
        bulles.append(f'<a href="{racine}gouvernorat/{slug}/" class="tn-b{" vide" if not n else ""}{" actif" if slug == actif else ""}" data-gouv="{slug}">'
                      f'<title>{E(fr)} · {ar} : {n}</title><circle cx="{x}" cy="{y}" r="{r}"/>' + (f'<text x="{x}" y="{y}">{n}</text>' if n else "") + "</a>")
    return (f'<svg class="carte-tn" viewBox="0 0 232 462" role="img" aria-label="Carte de la Tunisie : concours ouverts par gouvernorat">'
            f'<path class="tn-terre" d="{contour}"/><ellipse class="tn-terre" cx="{dj[0]}" cy="{dj[1]}" rx="9" ry="6.5"/>' + "".join(bulles) + "</svg>")


def hero_carte(ouverts, racine, texte, actif=""):
    """Bandeau : texte à gauche, carte de la Tunisie EN HAUT à droite (règle d'Ahmed, comme les annuaires)."""
    locaux = {}
    for c in ouverts:
        locaux[c["gouvernorat"]] = locaux.get(c["gouvernorat"], 0) + 1
    nat = locaux.get("national", 0)
    leg = (L(f"+ {nat} concours nationaux, ouverts partout. Touchez une bulle.", f"+ {ISO(nat)} مناظرة وطنية مفتوحة في كل مكان. المس دائرة.") if not actif
           else L("Autres gouvernorats : touchez la carte", "ولايات أخرى: المس الخريطة"))
    return (f'    <div class="hero-grille"><div class="hero-texte">\n{texte}\n    </div>'
            f'<figure class="hero-carte{" petite" if actif else ""}">{carte_tunisie(locaux, racine, actif)}<figcaption>{leg}</figcaption></figure></div>')


TYPES_ACTU = {t[0]: t for t in A.TYPES + [A.AUTRE]}
LIRE_AVIS = L("Lire l'avis sur le portail officiel", "اقرأ البلاغ في البوابة الرسمية")


def charger_actus():
    f = os.path.join(RACINE, "donnees", "actualites.json")
    return json.load(open(f, encoding="utf-8"))["actualites"] if os.path.exists(f) else []


def actu_html(x, racine):
    t = TYPES_ACTU.get(x["type"], A.AUTRE)
    liens = "".join(f'<a href="{racine}concours/{E(n)}/">{L(f"Concours n° {E(n)}", f"المناظرة عدد {ISO(E(n))}")}</a>' for n in x.get("concours", [])[:6])
    return (f'<article class="actu actu-{t[0]}"><p class="actu-haut"><span class="actu-type">{L(t[1], t[2])}</span>'
            f'<span class="actu-date">{ISO(dfr(x.get("date")))}</span></p>'
            f'<h3 dir="rtl" lang="ar">{E(x["organisme"])}</h3><p class="actu-resume" dir="rtl" lang="ar">{E(x["resume"])}</p>'
            + (f'<p class="actu-concours">{liens}</p>' if liens else "")
            + f'<a class="actu-lien" href="{E(x["lien"])}" target="_blank" rel="noopener">{LIRE_AVIS}{ICONE_LIEN}</a></article>')


def resultat(c):
    if c.get("source") == "finances":
        return L("sur la plateforme du ministère des Finances", "في منصة وزارة المالية")
    # « اطلاع » (consulter) = résultat publié ; « لم تنشر » (pas encore publié) ou « -- » (rien pour l'instant)
    if "اطلاع" in (c.get("resultat_final") or ""):
        return L("résultats définitifs publiés sur le portail", "النتائج النهائية منشورة في البوابة")
    if "اطلاع" in (c.get("resultat_initial") or ""):
        return L("résultats initiaux publiés sur le portail", "النتائج الأولية منشورة في البوابة")
    return L("pas encore publiés", "لم تنشر بعد")


URL_FINANCES = "https://concours.finances.gov.tn/"


def lien_officiel(c, detail=False):
    """Bouton vers le site officiel où l'on s'inscrit : le portail, ou la plateforme du ministère des Finances (2e source)."""
    if c.get("source") == "finances":
        lien = c.get("lien") if str(c.get("lien") or "").startswith(URL_FINANCES) else URL_FINANCES
        return (f'<a class="officiel" href="{E(lien)}" target="_blank" rel="noopener">'
                + L("Lire l'avis officiel et s'inscrire <small>(concours.finances.gov.tn)</small>", "اقرأ البلاغ الرسمي وترشح <small>(concours.finances.gov.tn)</small>")
                + f'{ICONE_LIEN}</a>')
    t = (L("S'inscrire ou voir le détail sur le portail officiel <small>(concours.gov.tn)</small>", "الترشح أو الاطلاع على التفاصيل في البوابة الرسمية <small>(concours.gov.tn)</small>") if detail
         else L("S'inscrire sur le portail officiel <small>(concours.gov.tn)</small>", "الترشح في البوابة الرسمية <small>(concours.gov.tn)</small>"))
    return f'<a class="officiel" href="{URL_PORTAIL}P1/index5.aspx?id=5" target="_blank" rel="noopener">{t}{ICONE_LIEN}</a>'


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
 {lien_officiel(c)}
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


def page(chemin, racine, titre, description, hero, contenu, v, maj, jsonld="", scripts=()):
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
{"".join(f'<script src="{racine}assets/{x}?v={v}"></script>'+chr(10) for x in scripts)}</head>
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
<footer id="pied"><div class="wrap"><p>Sources : portail officiel des concours publics (concours.gov.tn) et plateforme des concours du ministère des Finances (concours.finances.gov.tn) · © 2026 Alerte Concours Tunisie — tous droits réservés.</p></div></footer>
<script data-goatcounter="{COMPTEUR}/count" async src="https://gc.zgo.at/count.js"></script>
</body>
</html>
"""


def fil(racine, fr, ar):
    return f'    <p class="fil"><a href="{racine}">{L("Accueil", "الرئيسية")}</a> › {L(fr, ar)}</p>'


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


# ------------------------------------------------------------ Alertes concours (abonnement Telegram, 08/10/2026)
# Repris d'Alertes appels d'offres (même paiement en 3 étapes, même formulaire Formspree, même robot Telegram privé).
# Les abonnés (nom, téléphone, Telegram) ne sont JAMAIS dans ce dépôt public : dépôt privé « concours-abonnes ».
ABO = {
    "prix_3mois": 15, "prix_an": 39, "essai_jours": 7, "rappel_jours": 3,
    "numero": "24 321 390",                         # D17, IZI
    "whatsapp": "21624321390",                      # preuve de paiement
    "paiements": ["D17", "IZI"],
    "formspree": "https://formspree.io/f/mwlpakqj",
    "robot": "AlerteConcoursTunisieBot",            # robot Telegram créé par Ahmed le 08/10/2026 (jeton dans le dépôt privé concours-abonnes)
}
TEXTE_PREUVE = ("Bonjour, voici la preuve de paiement de mon abonnement Alertes concours "
                "(Alerte Concours Tunisie). Nom : ")
ICONE_CLOCHE = '<svg viewBox="0 0 24 24"><path d="M6 16.5V11a6 6 0 0 1 12 0v5.5l1.8 1.8H4.2z"/><path d="M10 20.5a2 2 0 0 0 4 0"/></svg>'
ICONE_WA = '<svg viewBox="0 0 24 24"><path d="M4 20l1.3-4A8 8 0 1 1 8.4 19z"/><path d="M9 8.6c0 3.4 2.9 6.4 6.4 6.4l1-1.4-2-1-1 .9c-1-.4-2.1-1.5-2.5-2.5l.9-1-1-2z"/></svg>'
APPLIS = {
    "D17": ("https://play.google.com/store/apps/details?id=tn.mobipost", "https://apps.apple.com/tn/app/digipostbank-d17/id1475640303"),
    "IZI": ("https://play.google.com/store/apps/details?id=tn.izi.consumer", "https://apps.apple.com/tn/app/izi/id1603653941"),
}
AIDE_TRANSFERT = '<details class="aide-transfert"><summary title="Voir comment faire" aria-label="Voir comment faire">?</summary><div class="aide-images"><figure><img src="RACINEassets/paiement/transfert-d17.svg" alt="Exemple D17 : Transfert rapide, numéro 24 321 390, montant, Envoyer" width="240" height="300" loading="lazy"><figcaption>D17</figcaption></figure><figure><img src="RACINEassets/paiement/transfert-izi.svg" alt="Exemple IZI : Transfert, montant, numéro 24 321 390, Suivant" width="240" height="300" loading="lazy"><figcaption>IZI</figcaption></figure></div></details>'


def prix_abo():
    m, a = ABO["prix_3mois"], ABO["prix_an"]
    return L(f"{m} DT / 3 mois <small>ou {a} DT / an</small>",
             f"{ISO(m)} دينار / ⁦3⁩ أشهر <small>أو {ISO(a)} دينار / سنة</small>")


def lien_preuve(ident="abo-preuve"):
    import urllib.parse
    url = f"https://wa.me/{ABO['whatsapp']}?text={urllib.parse.quote(TEXTE_PREUVE)}"
    return (f'<a class="btn-wa" id="{ident}" href="{E(url)}" data-texte="{E(TEXTE_PREUVE)}" target="_blank" rel="noopener">{ICONE_WA}'
            + L("Envoyer la preuve de paiement par WhatsApp", "أرسل إثبات الدفع عبر واتساب") + "</a>")


def liste_paiements(racine):
    applis = "".join(f'<a class="appli-btn" href="{APPLIS[m][0]}" target="_blank" rel="noopener noreferrer"><img src="{racine}assets/paiement/{m.lower()}.png" alt="{m}" width="44" height="44"></a>' for m in ABO["paiements"])
    ios = " · ".join(f'<a class="appli" href="{APPLIS[m][1]}" target="_blank" rel="noopener noreferrer">{m}</a>' for m in ABO["paiements"])
    e1, e1b = L("Ouvrez l'application :", 'افتح التطبيق:'), L('Sur iPhone :', 'على آيفون:')
    e2 = L('Dans D17 : « Transfert d’argent » puis « Transfert rapide ». Dans IZI : « Transfert ». Tapez le numéro', 'في D17: « تحويل الأموال » ثم « التحويل السريع ». في IZI: « تحويل ». أدخل الرقم')
    e2b, e3 = L('Montant :', 'المبلغ:'), L('Motif :', 'سبب الدفع:')
    e3b = L('Puis envoyez la capture du paiement par WhatsApp (bouton vert).', 'ثم أرسل لقطة الدفع عبر واتساب (الزر الأخضر).')
    conf = L("Vous payez directement dans l'application officielle de La Poste Tunisienne (D17) ou de Zitouna Paiement (IZI) : nous ne voyons jamais vos codes.", 'تدفع مباشرة في التطبيق الرسمي للبريد التونسي (D17) أو لزيتونة للدفع (IZI): لا نطّلع أبدًا على رموزك.')
    motif = L('votre nom et prénom', 'اسمك ولقبك')
    return (f'<div class="paie"><ol class="paie-etapes"><li>{e1} <span class="applis">{applis}</span><br><span class="petit">{e1b} {ios}</span></li>'
            f'<li>{e2} <strong><bdi dir="ltr">{ABO["numero"]}</bdi></strong>.<br>{e2b} <strong>{prix_abo()}</strong>{AIDE_TRANSFERT.replace("RACINE", racine)}</li>'
            f'<li>{e3} <strong>{motif}</strong>. {e3b}</li></ol><p class="paie-confiance">{conf}</p></div>')


def texte_telegram(robot):
    if robot:
        lien = f'<a href="https://t.me/{E(robot)}" target="_blank" rel="noopener"><bdi dir="ltr">@{E(robot)}</bdi></a>'
        return L(f"Ouvrez notre robot {lien} dans Telegram et envoyez <b>/start</b> suivi de votre code "
                 "(exemple : <code>/start AB12CD</code>). Le code vous est donné à l'activation.",
                 f"افتح برنامجنا {lien} في تيليغرام وأرسل <b><bdi dir=\"ltr\">/start</bdi></b> متبوعًا برمزك "
                 "(مثال: <code dir=\"ltr\">/start AB12CD</code>). يُعطى لك الرمز عند التفعيل.")
    return L("Le lien Telegram vous est envoyé à l'activation, avec votre code personnel : il suffira d'ouvrir notre robot "
             "et d'envoyer <b>/start</b> suivi de votre code.",
             "يُرسل إليك رابط تيليغرام عند التفعيل مع رمزك الشخصي: يكفي أن تفتح برنامجنا وترسل "
             "<b><bdi dir=\"ltr\">/start</bdi></b> متبوعًا برمزك.")


def bouton_alertes(racine):
    """Gros bouton doré (comme Alertes appels d'offres) -> page alertes/ (inscription)."""
    n = ABO["essai_jours"]
    titre = L("Alertes concours : votre métier et votre gouvernorat chaque matin sur Telegram", "تنبيهات المناظرات: اختصاصك وولايتك كل صباح على تيليغرام")
    sous = L(f"{n} jours d'essai gratuit · suivi de vos concours (convocations, résultats)",
             f"تجربة مجانية {ISO(n)} أيام · متابعة مناظراتك (الاستدعاءات، النتائج)")
    return (f'<a class="btn-pro-grand" id="btn-alertes" href="{racine}alertes/">{ICONE_CLOCHE}'
            f'<span>{titre}<small>{sous}</small></span></a>')


def pages_alertes(v, maj):
    """Page alertes/ (offre, paiement, inscription) et alertes/conditions/."""
    essai, p3, pa, rj = ABO["essai_jours"], ABO["prix_3mois"], ABO["prix_an"], ABO["rappel_jours"]
    cases_m = "".join(f'<label class="case"><input type="checkbox" name="metiers" value="{s}"> <span>{L(E(fr), ar)}</span></label>' for s, fr, ar in METIERS)
    cases_g = (f'<label class="case tous"><input type="checkbox" name="gouvernorats" value="tous" id="g-tous"> <span><b>{L("Toute la Tunisie", "كل الولايات")}</b></span></label>'
               + "".join(f'<label class="case"><input type="checkbox" name="gouvernorats" value="{s}"> <span>{L(E(fr), ar)}</span></label>' for s, fr, ar in GOUVS))
    accepte = L('J\'accepte les <a href="conditions/">conditions de l\'abonnement</a>.', 'أوافق على <a href="conditions/">شروط الاشتراك</a>.')
    hero = f"""{fil("../", "Alertes", "التنبيهات")}
    <h1>{L("Alertes concours sur Telegram", "تنبيهات المناظرات على تيليغرام")}</h1>
    <p class="intro">{L("Chaque matin, seulement les nouveaux concours de VOTRE métier et de VOTRE gouvernorat, et le suivi des concours que vous passez. La liste complète reste gratuite sur ce site.",
                        "كل صباح، المناظرات الجديدة في اختصاصك وولايتك فقط، مع متابعة المناظرات التي تشارك فيها. القائمة الكاملة تبقى مجانية في هذا الموقع.")}</p>"""
    contenu = f"""<section class="offre-pro" id="offre">
  <p class="ruban">{L(f"{essai} jours d'essai gratuit", f"تجربة مجانية {ISO(essai)} أيام")}</p>
  <h2>{L("Alertes + Suivi", "التنبيهات + المتابعة")}</h2>
  <p class="prix" id="abo-prix">{prix_abo()}</p>
  <ul class="avantages masque-si-paiement">
    <li>{L("Un message chaque matin sur <b>Telegram</b> : les nouveaux concours de vos métiers et de vos gouvernorats, plus les concours nationaux (ouverts à toute la Tunisie)", "رسالة كل صباح على <b>تيليغرام</b>: المناظرات الجديدة في اختصاصاتك وولاياتك، مع المناظرات الوطنية (المفتوحة لكل الجمهورية)")}</li>
    <li>{L("Un rappel 3 jours avant la date limite d'inscription", "تذكير قبل آخر أجل للترشح بـ⁦3⁩ أيام")}</li>
    <li>{L("<b>Suivi</b> des concours que vous choisissez : candidatures acceptées, convocations, report, résultats", "<b>متابعة</b> المناظرات التي تختارها: قبول الترشحات، الاستدعاءات، التأجيل، النتائج")}</li>
    <li>{L("Pour chaque concours : nombre de postes, date limite et lien vers le portail officiel", "لكل مناظرة: عدد الخطط، آخر أجل ورابط البوابة الرسمية")}</li>
    <li>{L(f"Pas de renouvellement automatique : rappel {rj} jours avant la fin, puis l'alerte s'arrête simplement", f"لا تجديد آلي: تذكير قبل النهاية بـ{ISO(rj)} أيام، ثم يتوقف التنبيه ببساطة")}</li>
  </ul>
  <p class="petit masque-si-paiement">{L(f"{essai} jours d'essai gratuit, sans paiement. Ensuite, paiement par D17 ou IZI (bouton « Paiement »). Frais de l'application (environ 2 DT) en plus.",
                      f"تجربة مجانية لمدة {ISO(essai)} أيام دون دفع. بعدها، الدفع عبر ⁨D17⁩ أو ⁨IZI⁩ (زر «الدفع»). معاليم التطبيق (حوالي ⁦2⁩ د) إضافية.")}</p>
  <details class="paiement" id="paiement"><summary class="btn-clair">{L("Paiement", "الدفع")}</summary>
    {liste_paiements("../")}
    {lien_preuve()}
  </details>
  <a class="btn-pro" href="#inscription">{L(f"Je m'inscris : {essai} jours gratuits", f"أسجّل: {ISO(essai)} أيام مجانًا")}</a>
</section>
<section class="carte">
  <h2>{L("Comment ça marche ?", "كيف يعمل؟")}</h2>
  <ol class="etapes" data-l="fr">
    <li>Vous choisissez vos <b>métiers</b> et vos <b>gouvernorats</b> dans le formulaire ci-dessous (et, si vous voulez, les numéros des concours à suivre).</li>
    <li>Nous activons votre abonnement (en général sous 24 heures) et vous envoyons votre <b>code personnel</b>.</li>
    <li>Dans Telegram, vous ouvrez notre robot et envoyez <b>/start</b> suivi de votre code.</li>
    <li>Chaque matin, vous recevez les nouveaux concours qui vous concernent. Pour suivre un concours de plus, envoyez au robot <b>/suivre</b> et son numéro (exemple : <code>/suivre 2390</code>).</li>
  </ol>
  <ol class="etapes" data-l="ar">
    <li>تختار <b>اختصاصاتك</b> و<b>ولاياتك</b> في الاستمارة أسفله (وأرقام المناظرات التي تريد متابعتها إن شئت).</li>
    <li>نفعّل اشتراكك (عادة في غضون ⁦24⁩ ساعة) ونرسل إليك <b>رمزك الشخصي</b>.</li>
    <li>في تيليغرام، تفتح برنامجنا وترسل <b><bdi dir="ltr">/start</bdi></b> متبوعًا برمزك.</li>
    <li>كل صباح، تصلك المناظرات الجديدة التي تهمّك. لمتابعة مناظرة أخرى، أرسل إلى البرنامج <b><bdi dir="ltr">/suivre</bdi></b> ورقمها (مثال: <code dir="ltr">/suivre 2390</code>).</li>
  </ol>
</section>
<section class="carte abo" id="inscription" aria-labelledby="abo-titre">
  <h2 id="abo-titre">{L("Inscription", "التسجيل")}</h2>
  <form id="abo-form" action="{ABO['formspree']}" method="POST" novalidate>
    <label class="abo-etiquette" for="abo-nom">{L("Votre nom et prénom (motif du paiement)", "اسمك ولقبك (سبب الدفع)")}</label>
    <input id="abo-nom" name="nom" required maxlength="100" autocomplete="name">
    <label class="abo-etiquette" for="abo-tel">{L("Téléphone (8 chiffres)", "الهاتف (⁦8⁩ أرقام)")}</label>
    <input id="abo-tel" name="telephone" required inputmode="tel" pattern="[0-9 ]{{8,11}}" maxlength="11" autocomplete="tel">
    <label class="abo-etiquette" for="abo-email">{L("E-mail (facultatif)", "البريد الإلكتروني (اختياري)")}</label>
    <input id="abo-email" type="email" name="email" maxlength="200" autocomplete="email">
    <fieldset class="abo-choix" id="abo-metiers">
      <legend>{L("Vos métiers (un ou plusieurs)", "اختصاصاتك (واحد أو أكثر)")}</legend>
      <div class="cases">{cases_m}</div>
    </fieldset>
    <fieldset class="abo-choix" id="abo-gouv">
      <legend>{L("Vos gouvernorats (les concours nationaux sont toujours inclus)", "ولاياتك (المناظرات الوطنية مضمّنة دائمًا)")}</legend>
      <div class="cases">{cases_g}</div>
    </fieldset>
    <label class="abo-etiquette" for="abo-suivis">{L("Concours à suivre (facultatif) : leurs numéros, séparés par des virgules", "مناظرات للمتابعة (اختياري): أرقامها مفصولة بفواصل")}</label>
    <input id="abo-suivis" name="suivis" maxlength="120" inputmode="numeric" placeholder="2390, 2412">
    <fieldset class="abo-choix" id="abo-formule">
      <legend>{L("Votre formule", "صيغتك")}</legend>
      <label class="case"><input type="radio" name="formule" value="essai {essai} jours" checked> <span>{L(f"<b>{essai} jours d'essai gratuit</b>, je paierai ensuite si je suis satisfait", f"<b>تجربة مجانية {ISO(essai)} أيام</b>، وأدفع بعدها إن كنت راضيًا")}</span></label>
      <label class="case"><input type="radio" name="formule" value="3 mois"> <span>{L(f"Je paie directement 3 mois ({p3} DT)", f"أدفع مباشرة ⁦3⁩ أشهر ({ISO(p3)} دينار)")}</span></label>
      <label class="case"><input type="radio" name="formule" value="1 an"> <span>{L(f"Je paie directement 1 an ({pa} DT)", f"أدفع مباشرة سنة ({ISO(pa)} دينار)")}</span></label>
    </fieldset>
    <label class="case"><input type="checkbox" name="conditions" value="oui" required id="abo-conditions"> <span>{accepte}</span></label>
    <input type="hidden" name="site" value="Alerte Concours Tunisie">
    <input type="hidden" name="page" value="">
    <input type="hidden" name="_subject" value="Abonnement Alertes concours — Alerte Concours Tunisie">
    <input type="text" name="_gotcha" class="abo-piege" tabindex="-1" autocomplete="off" aria-hidden="true">
    <button type="submit" class="btn-pro">{L("Envoyer mon inscription", "أرسل تسجيلي")}</button>
    <p id="abo-status" role="status" aria-live="polite"></p>
    <p class="petit">{L("Vos coordonnées servent seulement à l'abonnement : elles ne sont jamais publiées ni vendues (envoi par le service Formspree). Rien n'est envoyé sans clic sur « Envoyer ».",
                        "تُستعمل بياناتك للاشتراك فقط: لا تُنشر ولا تُباع أبدًا (إرسال عبر خدمة ⁨Formspree⁩). لا يُرسل أي شيء دون الضغط على «أرسل».")}</p>
  </form>
  <div class="apres-abo" id="apres-abo" hidden>
    <h3>{L("Merci, votre inscription est bien reçue", "شكرًا، وصلنا تسجيلك")}</h3>
    <p>{L(f"Nous activons votre abonnement, en général sous 24 heures. Vos {essai} jours d'essai gratuit commencent à l'activation.", f"نفعّل اشتراكك عادة في غضون ⁦24⁩ ساعة. تبدأ أيامك المجانية الـ{ISO(essai)} عند التفعيل.")}</p>
    <h3>{L("Recevoir les alertes sur Telegram", "تلقي التنبيهات على تيليغرام")}</h3>
    <p id="abo-telegram">{texte_telegram(ABO["robot"])}</p>
    <p class="petit">{L("Installez Telegram (gratuit) sur votre téléphone si ce n'est pas déjà fait.", "ثبّت تيليغرام (مجاني) على هاتفك إن لم يكن مثبتًا.")}</p>
    <h3>{L("Paiement", "الدفع")}</h3>
    <p>{L("Après l'essai (ou tout de suite si vous avez choisi de payer directement), payez par D17 ou IZI, avec pour motif votre nom et prénom :", "بعد التجربة (أو فورًا إن اخترت الدفع مباشرة)، ادفع عبر ⁨D17⁩ أو ⁨IZI⁩ مع ذكر اسمك ولقبك كسبب للدفع:")}</p>
    {liste_paiements("../")}
    {lien_preuve("abo-preuve-apres")}
    <p class="petit">{L(f"Pas de renouvellement automatique : nous vous prévenons {rj} jours avant la fin.", f"لا تجديد آلي: نعلمك قبل النهاية بـ{ISO(rj)} أيام.")}</p>
  </div>
</section>
<p class="avert">{L("La liste des concours reste <b>gratuite, sans inscription</b>, sur ce site. L'abonnement ajoute seulement l'alerte personnalisée et le suivi sur Telegram. Ce site n'est pas officiel : l'inscription aux concours se fait toujours sur le portail officiel.",
                    "قائمة المناظرات تبقى <b>مجانية ودون تسجيل</b> في هذا الموقع. الاشتراك يضيف فقط التنبيه الشخصي والمتابعة على تيليغرام. هذا الموقع ليس رسميًا: الترشح يتم دائمًا في البوابة الرسمية.")}</p>
{AVIS}"""
    titre = f"Alertes concours Tunisie sur Telegram : votre métier, votre gouvernorat — {essai} jours gratuits | Alerte Concours Tunisie"
    desc = (f"Recevez chaque matin sur Telegram les nouveaux concours publics de votre métier et de votre gouvernorat, et le suivi de vos concours "
            f"(convocations, résultats). {p3} DT / 3 mois ou {pa} DT / an, {essai} jours d'essai gratuit, sans renouvellement automatique.")
    res = {"alertes/": page("alertes/", "../", titre, desc, hero, contenu, v, maj, scripts=("abonnement.js",))}

    hero = f"""    <p class="fil"><a href="../../">{L("Accueil", "الرئيسية")}</a> › <a href="../">{L("Alertes", "التنبيهات")}</a> › {L("Conditions", "الشروط")}</p>
    <h1>{L("Conditions de l'abonnement", "شروط الاشتراك")}</h1>
    <p class="intro">{L("Alertes concours : prix, essai gratuit, paiement, données personnelles, arrêt.", "تنبيهات المناظرات: السعر، التجربة المجانية، الدفع، المعطيات الشخصية، الإيقاف.")}</p>"""
    num = ABO["numero"]
    sections = [
        ("1. Le service", "1. الخدمة",
         "Alertes concours envoie chaque matin sur Telegram les nouveaux concours publics correspondant aux métiers et aux gouvernorats choisis par l'abonné, ainsi que les concours nationaux de ses métiers, un rappel avant la date limite d'inscription, et les nouvelles (candidatures acceptées, convocations, report, résultats) des concours qu'il suit. La liste des concours reste gratuite et sans inscription sur le site.",
         "ترسل تنبيهات المناظرات كل صباح على تيليغرام المناظرات العمومية الجديدة المطابقة للاختصاصات والولايات التي اختارها المشترك، والمناظرات الوطنية في اختصاصاته، وتذكيرًا قبل آخر أجل للترشح، وأخبار المناظرات التي يتابعها (قبول الترشحات، الاستدعاءات، التأجيل، النتائج). قائمة المناظرات تبقى مجانية ودون تسجيل في الموقع."),
        ("2. Prix", "2. السعر",
         f"{p3} DT pour 3 mois ou {pa} DT pour un an, en dinars tunisiens. Les frais de l'application de paiement (environ 2 DT) sont à la charge de l'abonné. Le prix affiché au moment de l'inscription s'applique à toute la période payée.",
         f"{ISO(p3)} دينار لـ⁦3⁩ أشهر أو {ISO(pa)} دينار للسنة. معاليم تطبيق الدفع (حوالي ⁦2⁩ د) على حساب المشترك. السعر المعروض عند التسجيل يُطبَّق على كامل المدة المدفوعة."),
        ("3. Essai gratuit", "3. التجربة المجانية",
         f"Les {essai} premiers jours sont gratuits, sans paiement et sans engagement. Sans paiement à la fin de l'essai, l'alerte s'arrête simplement.",
         f"الأيام الـ{ISO(essai)} الأولى مجانية، دون دفع ودون التزام. إذا لم يتم الدفع في نهاية التجربة، يتوقف التنبيه ببساطة."),
        ("4. Paiement", "4. الدفع",
         f"Paiement par D17 ou IZI au {num}, avec pour motif le nom et prénom de l'abonné, puis preuve envoyée par WhatsApp au même numéro. La période payée commence après l'essai gratuit ou après la période déjà payée.",
         f"الدفع عبر ⁨D17⁩ أو ⁨IZI⁩ على الرقم {ISO(num)} مع ذكر اسم المشترك ولقبه، ثم إرسال الإثبات عبر واتساب على نفس الرقم. تبدأ المدة المدفوعة بعد التجربة المجانية أو بعد المدة المدفوعة سابقًا."),
        ("5. Pas de renouvellement automatique", "5. لا تجديد آلي",
         f"Il n'y a aucun renouvellement automatique : un rappel est envoyé {rj} jours avant la fin ; sans nouveau paiement, l'alerte s'arrête simplement à la date de fin.",
         f"لا يوجد أي تجديد آلي: يُرسل تذكير قبل النهاية بـ{ISO(rj)} أيام، ودون دفع جديد يتوقف التنبيه ببساطة في تاريخ النهاية."),
        ("6. Arrêt", "6. الإيقاف",
         "L'abonné peut arrêter les alertes à tout moment, en envoyant /stop au robot Telegram ou en nous écrivant sur WhatsApp. Pendant l'essai gratuit, rien n'est dû. Une période déjà payée n'est pas renouvelée.",
         "يمكن للمشترك إيقاف التنبيهات في أي وقت بإرسال ⁨/stop⁩ إلى برنامج تيليغرام أو بمراسلتنا عبر واتساب. خلال التجربة المجانية لا يُستحق أي مبلغ. المدة المدفوعة لا تُجدَّد."),
        ("7. Limites", "7. الحدود",
         "Les concours et les nouvelles viennent du portail officiel des concours publics (concours.gov.tn). Le classement par métier et par gouvernorat est automatique et peut se tromper ; une annonce peut manquer si le portail est en panne. Seul le portail officiel fait foi : vérifiez toujours l'avis officiel. Ce site n'est pas officiel et ne s'occupe pas de votre candidature.",
         "المناظرات والأخبار مصدرها البوابة الرسمية للمناظرات العمومية (concours.gov.tn). الترتيب حسب الاختصاص والولاية آلي وقد يخطئ، وقد يغيب إعلان إذا تعطلت البوابة. البوابة الرسمية هي المرجع الوحيد: اطّلع دائمًا على البلاغ الرسمي. هذا الموقع ليس رسميًا ولا يتولى ترشحك."),
        ("8. Données personnelles", "8. المعطيات الشخصية",
         "Nous gardons seulement : nom, téléphone, e-mail s'il est donné, métiers, gouvernorats et concours suivis, dates de l'abonnement et identifiant Telegram. Elles servent uniquement à envoyer les alertes, sont conservées dans un espace privé, ne sont jamais publiées ni vendues, et sont supprimées sur simple demande (WhatsApp). Le formulaire passe par le service Formspree et les alertes par Telegram.",
         "نحتفظ فقط بـ: الاسم، الهاتف، البريد الإلكتروني إن وُجد، الاختصاصات والولايات والمناظرات المتابَعة، تواريخ الاشتراك ومعرّف تيليغرام. تُستعمل فقط لإرسال التنبيهات، وتُحفظ في فضاء خاص، ولا تُنشر ولا تُباع أبدًا، وتُحذف بمجرد الطلب (واتساب). تمر الاستمارة عبر خدمة ⁨Formspree⁩ والتنبيهات عبر تيليغرام."),
        ("9. Contact", "9. الاتصال", f"WhatsApp : {num}.", f"واتساب: {ISO(num)}."),
    ]
    corps = "\n".join(f"  <h2>{L(a, b)}</h2>\n  <p>{L(c, d)}</p>" for a, b, c, d in sections)
    contenu = f"""<section class="carte conditions">
{corps}
  <p><a class="btn-pro" href="../#inscription">{L("Retour à l'inscription", "العودة إلى التسجيل")}</a></p>
</section>"""
    titre = "Conditions de l'abonnement Alertes concours (Telegram) | Alerte Concours Tunisie"
    desc = (f"Conditions d'Alertes concours : {p3} DT / 3 mois ou {pa} DT / an, {essai} jours d'essai gratuit, "
            "pas de renouvellement automatique, paiement D17 ou IZI, données personnelles et arrêt.")
    res["alertes/conditions/"] = page("alertes/conditions/", "../../", titre, desc, hero, contenu, v, maj)
    return res


def ecrire(chemin, contenu):
    f = os.path.join(RACINE, chemin, "index.html") if not chemin.endswith(".html") else os.path.join(RACINE, chemin)
    os.makedirs(os.path.dirname(f), exist_ok=True)
    open(f, "w", encoding="utf-8", newline="\n").write(contenu)


def construire(jour):
    d, ouverts = charger(jour)
    maj = d.get("lu_le", "")
    v = hashlib.sha1("".join(open(os.path.join(RACINE, "assets", f), "rb").read().decode("utf-8", "ignore") for f in ("style.css", "page.js", "app.js", "avis.js", "abonnement.js")).encode()).hexdigest()[:8]
    cm, cg = comptes(ouverts)
    urgents = sum(1 for c in ouverts if c.get("cloture_candidatures") and 0 <= (dt.date.fromisoformat(c["cloture_candidatures"]) - dt.date.fromisoformat(jour)).days < 7)
    postes = sum(c.get("postes") or 0 for c in ouverts)
    pages = {}
    actus = charger_actus()

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
{f'<h2 class="titre-section" id="actualites">{L("Dernières actualités des concours", "آخر أخبار المناظرات")}</h2><div class="actus">{"".join(actu_html(x, "") for x in actus[:4])}</div><p><a class="btn" href="actualites/">{L("Toutes les actualités (résultats, convocations…)", "كل الأخبار (النتائج، الاستدعاءات…)")}</a></p>' if actus else ""}
<section class="carte"><h2>{L("Comment s'inscrire ?", "كيف تترشح؟")}</h2><p>{L("L'inscription se fait toujours sur le portail officiel. Notre guide explique les étapes une par une.", "الترشح يتم دائمًا في البوابة الرسمية. دليلنا يشرح المراحل واحدة بواحدة.")}</p>
<a class="btn" href="guide-inscription/">{L("Lire le guide d'inscription", "اقرأ دليل الترشح")}</a></section>
{AVIS}"""
    hero = hero_carte(ouverts, "", hero)
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
        if s != "national":
            hero = hero_carte(ouverts, "../../", hero, s)
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
{lien_officiel(c, detail=True)}
<p class="note">{L("Informations reprises du tableau officiel des concours publics. Seul le portail officiel fait foi : lisez toujours l'avis officiel (conditions, pièces, dates).", "معطيات مأخوذة من الجدول الرسمي للمناظرات العمومية. البوابة الرسمية هي المرجع الوحيد: اطّلع دائمًا على البلاغ الرسمي (الشروط، الوثائق، الآجال).")}</p></section>
<section class="carte"><h2>{L("Comment s'inscrire ?", "كيف تترشح؟")}</h2><p>{L("Sur le portail officiel, avec le numéro de votre carte d'identité. Notre guide explique les étapes une par une.", "في البوابة الرسمية، برقم بطاقة التعريف الوطنية. دليلنا يشرح المراحل واحدة بواحدة.")}</p>
<a class="btn" href="../../guide-inscription/">{L("Lire le guide d'inscription", "اقرأ دليل الترشح")}</a></section>
{bouton_alertes("../../")}
{(lambda la: f'<h2 class="titre-section">{L("Actualités de cet organisme", "أخبار هذا الهيكل")}</h2><div class="actus">{"".join(actu_html(x, "../../") for x in la)}</div>' if la else "")([x for x in actus if c["id"] in x.get("concours", [])][:6])}
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

    # --- actualités du portail (08/10/2026) : nouveaux concours, candidatures acceptées, convocations, résultats, reports
    if actus:
        compte_t = {}
        for x in actus: compte_t[x["type"]] = compte_t.get(x["type"], 0) + 1
        puces = "".join(f'<a class="pastille" href="#t-{k}">{L(TYPES_ACTU[k][1], TYPES_ACTU[k][2])} ({n})</a>' for k, n in compte_t.items())
        blocs = ""
        for k in [t[0] for t in A.TYPES + [A.AUTRE]]:
            la = [x for x in actus if x["type"] == k]
            if la:
                blocs += f'<h2 class="titre-section" id="t-{k}">{L(TYPES_ACTU[k][1], TYPES_ACTU[k][2])}</h2><div class="actus">{"".join(actu_html(x, "../") for x in la)}</div>'
        hero = f"""{fil("../", "Actualités", "الأخبار")}
    <h1>{L("Actualités des concours : résultats, convocations, candidatures acceptées", "أخبار المناظرات: النتائج، الاستدعاءات، قبول الترشحات")}</h1>
    <p class="intro">{L(f"Les {len(actus)} derniers avis publiés sur le portail officiel des concours publics, classés par type. Mis à jour chaque jour.", f"آخر {ISO(len(actus))} بلاغًا منشورًا في البوابة الرسمية للمناظرات العمومية، مصنفة حسب النوع. تحيين يومي.")}</p>"""
        contenu = f"""<section class="carte"><p class="puces-actu">{puces}</p>
<p class="note">{L("Résumés des avis officiels. Lisez toujours l'avis complet sur le portail officiel : seul lui fait foi.", "ملخصات للبلاغات الرسمية. اقرأ دائمًا البلاغ كاملًا في البوابة الرسمية: هي المرجع الوحيد.")}</p></section>
{blocs}
{bouton_alertes("../")}"""
        pages["actualites/"] = page("actualites/", "../", "Actualités des concours en Tunisie : résultats, convocations, admis | Alerte Concours Tunisie",
                                    f"Résultats, listes des admis, convocations et nouveaux concours publiés sur le portail officiel des concours publics : {len(actus)} avis, mis à jour chaque jour. نتائج المناظرات.",
                                    hero, contenu, v, maj)

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

    # --- alertes (abonnement Telegram) et conditions
    pages.update(pages_alertes(v, maj))

    # --- à propos
    hero = f"""{fil("../", "À propos et sources", "من نحن والمصادر")}
    <h1>{L("À propos et sources", "من نحن والمصادر")}</h1>"""
    contenu = f"""<section class="carte"><h2>{L("D'où viennent les concours ?", "من أين تأتي المناظرات؟")}</h2>
<p>{L("Chaque jour, un robot lit le tableau officiel des concours ouverts du portail des concours publics (www.concours.gov.tn) : organisme, grade, nombre de postes, dates et état des résultats. Le gouvernorat est déduit du nom de l'organisme ; un concours national est ouvert à toute la Tunisie. Il lit aussi la plateforme officielle des concours du ministère des Finances (concours.finances.gov.tn) : ces concours sont nationaux.",
       "كل يوم، يقرأ برنامج آلي الجدول الرسمي للمناظرات المفتوحة في بوابة المناظرات العمومية (www.concours.gov.tn): الهيكل، الخطة، عدد الخطط، الآجال وحالة النتائج. تُستنتج الولاية من اسم الهيكل؛ والمناظرة الوطنية مفتوحة لكل الجمهورية. كما يقرأ المنصة الرسمية لمناظرات وزارة المالية (concours.finances.gov.tn): وهي مناظرات وطنية.")}</p>
<p>{L("Ce site est indépendant et non officiel. Seul le portail officiel fait foi, et l'inscription se fait toujours sur le site officiel.", "هذا الموقع مستقل وغير رسمي. البوابة الرسمية هي المرجع الوحيد، والترشح يتم دائمًا في الموقع الرسمي.")}</p></section>
{AVIS}"""
    pages["a-propos/"] = page("a-propos/", "../", "À propos et sources | Alerte Concours Tunisie", "D'où viennent les concours d'Alerte Concours Tunisie : le portail officiel des concours publics et la plateforme du ministère des Finances.", hero, contenu, v, maj)

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
