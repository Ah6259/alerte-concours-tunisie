# Alerte Concours Tunisie (alerte-concours-tunisie)

Fichier lu par Claude Code au début de chaque session. **Dépôt PUBLIC : rien de personnel ni de secret, jamais le nom
d'un site concurrent.** Répondre à Ahmed **en français**, simplement.

## AVANT TOUT : récupérer le travail fait ailleurs
Ahmed travaille depuis le PC ET depuis son téléphone. Toujours `git pull` avant de modifier (sur le PC : « fais git pull
partout »), et commit + push à la fin. Rien ne doit rester seulement sur le PC.
Sur un nouveau PC, avant le premier commit : `git config user.name Ah6259` et
`git config user.email 200752748+Ah6259@users.noreply.github.com`.

## Ce que sera le site (décisions d'Ahmed du 08/10/2026)
- **Tous les gouvernorats** : chaque concours est classé par gouvernorat (déduit de l'organisme) et par métier ;
  un concours « national » (ministère, office national…) est ouvert à toute la Tunisie et apparaît sur la page de
  CHAQUE gouvernorat. Pages : accueil (filtres gouvernorat + métier, compte à rebours de la date limite), une page par
  gouvernorat, une par métier, une par concours (lien officiel), guide « s'inscrire sur concours.gov.tn ».
- **Alertes Pro (Telegram)** : choix du métier ET du gouvernorat (national inclus) ; **Suivi** des concours choisis
  (l'état des résultats du tableau officiel change → message). **Entraînement** : QCM écrits par nous.
- **Page `alertes/` OUVERTE (08/10/2026, « fais » d'Ahmed)** : offre + paiement en 3 étapes + formulaire Formspree
  (nom, téléphone, e-mail facultatif, métiers, gouvernorats ou « Toute la Tunisie », numéros de concours à suivre,
  formule essai **7 jours** / 3 mois / 1 an) + `alertes/conditions/` ; `assets/abonnement.js` (ligne « pour_activer »).
  Gros bouton doré `bouton_alertes()` sur toutes les pages. Réglages : `ABO` de construire_site.py (`robot` = **@AlerteConcoursTunisieBot**, créé le 08/10 ;
  son jeton = secret `TELEGRAM_BOT_TOKEN` du dépôt privé, jamais ailleurs). **Abonnés = dépôt PRIVÉ `concours-abonnes`** (jamais ici).
- **Prix** (frais D17 / IZI d'environ 2 DT payés par le client en plus) : Alertes + Suivi 15 DT / 3 mois ou
  39 DT / an ; Entraînement 19 DT / 30 jours ou 29 DT / 90 jours ; Pack complet 49 DT / an.
- Règles communes à tous les sites d'Ahmed : `../../regles communes a tous les sites.md` (paiement en 3 étapes,
  description cachée à l'ouverture du paiement, tests + sabotage + gendarmes, portail + vidéo dès la mise en ligne…).

## Sources (faits publics + lien officiel, jamais le texte entier)
- www.concours.gov.tn, `P1/index5.aspx?id=5` : tableau officiel (ASP.NET, 5 lignes par page, page suivante =
  formulaire caché `__EVENTTARGET=GVConcoursPublic` / `__EVENTARGUMENT=Page$Next`). Pas de robots.txt. Robot lent (2 s).
- À ajouter : actualités du portail (`P1/index31.aspx?id=<n>`) et ANETI (`emploi.nat.tn/fo/Fr/global.php?page=21`,
  détail `page=198&ref=<n>`, robots.txt : tout autorisé).

## Gouvernorats
`robot/gouvernorats.py` : délégations (`delegations_ar.json`, référentiel du Registre national des entreprises) +
387 noms de municipalités et leur wilaya (`municipalites_ar.json`, d'après Wikipédia en arabe « قائمة بلديات تونس »).
Le 08/10/2026 : 143 lignes lues, toutes les municipalités du jour classées ; « national » pour ministères et offices.
Un organisme mal classé → ajouter son lieu, puis un cas dans `tools/test_robot.py`.

## Pages (robot/construire_site.py)
Accueil (résumé, « se terminent bientôt », filtres, liste, gouvernorats, métiers, guide, avis), `gouvernorat/<slug>/`
(24 + `national`), `metier/<slug>/`, **`concours/<n°>/`** (08/10/2026 : une page par concours du tableau, ouvert ou clos :
grade, organisme, postes, dates, résultats, lien officiel, guide, concours proches ; le grade des cartes y mène), `guide-inscription/` (d'après le guide officiel du candidat), `alertes/` (bientôt),
`a-propos/` ; sitemap, robots.txt (IA refusées), manifeste, service worker. Gabarit, styles et scripts repris
d'Alertes appels d'offres (couleur verte #1F6B60) ; `assets/app.js` : filtre gouvernorat = ses concours + les nationaux.
**Actualités du portail** (08/10/2026) : `robot/lire_actualites.py` (liste P1/index15.aspx?id=pub, détail index31 ; 40 la 1re fois,
ensuite les nouvelles, 300 gardées ; résumé ≤ 300 caractères ; types résultats / report / convocation / candidatures / nouveau /
autre ; rattachées aux concours du même organisme) → `donnees/actualites.json` → page `actualites/`, 4 dernières sur l'accueil,
« Actualités de cet organisme » sur la page d'un concours. Panne : ancien fichier gardé, le site n'est pas bloqué.
ANETI (emploi.nat.tn) : REFUSE les connexions depuis GitHub et depuis l'ordinateur de Claude (essai du 08/10/2026 : « connection reset »),
il ne répond qu'aux connexions de Tunisie (PC d'Ahmed) → pas utilisé pour l'instant (règle « tout sans PC ») ; le portail officiel suffit.
**Carte de la Tunisie EN HAUT du bandeau** (08/10/2026, règle d'Ahmed, comme les annuaires) : `carte_tunisie` / `hero_carte`, bulle = concours des organismes du gouvernorat
(+ nationaux indiqués sous la carte) ; accueil et pages de gouvernorat (la sienne en or) ; app.js ne recompte que sur l'accueil.
Construire : `python robot/construire_site.py [--aujourdhui AAAA-MM-JJ]`.
Tests : `python tools/test_robot.py` (29) et `node tools/test_site.mjs` (61, jsdom ; dont les pages des concours, sabotage vérifié) — sabotage vérifié le 08/10 (filtre
national cassé → détecté).

## État au 08/10/2026
Fait : robot, classement métier / gouvernorat, pages FR + AR, tests, publication GitHub Pages.
À faire : portail + vidéo, Search Console, vérification du matin et gendarme IA (ajouter ce dépôt à leurs sources),
 Alertes / Suivi (Telegram, paiement 3 étapes), puis Entraînement.

## Autres sources officielles testées depuis GitHub (08/10/2026, demande d'Ahmed : « des concours dans tous les gouvernorats »)
Constat : le portail n'a des concours LOCAUX que dans 9 gouvernorats (Kébili, Nabeul, Tunis, Jendouba, Bizerte, Sousse,
Monastir, Kairouan, Manouba) ; classement vérifié juste. Test par le robot `tester-source.yml` du dépôt prix-eaux-tunisie :
- LISIBLES : concours.finances.gov.tn (tableau clair : grade, spécialité, postes, dates, avis) ; education.gov.tn,
  interieur.gov.tn, mes.tn, cnss.tn (certificat incomplet → `curl -k`) ; pm.gov.tn ; steg.com.tn.
- NON JOIGNABLES : collectivites-locales.gov.tn et santetunisie.rns.tn (adresse introuvable), defense.tn (délai),
  emploi.gov.tn, iort.gov.tn (page vide). BLOQUÉS anti-robot (pas de contournement) : douane.gov.tn, sonede.com.tn.
- Ces sources sont surtout NATIONALES (ministères) : elles ajoutent des concours ouverts à tous, pas des concours locaux.
  Aucune source officielle centrale des communes / hôpitaux régionaux n'est lisible depuis GitHub.
Rien n'est ajouté au site sans l'accord d'Ahmed.
- **AJOUTÉ (08/10/2026, « fais 1 » d'Ahmed) : ministère des Finances** = `robot/lire_finances.py`, appelé par lire_concours.py :
  une ligne par grade, numéros **900000 + 100 × n° de l'annonce + rang** (jamais ceux du portail), gouvernorat « national »,
  `source: "finances"`, `lien` = avis officiel (PDF) ; clos depuis plus de 60 jours = pas repris ; même date limite qu'un concours
  « المالية » du portail = doublon écarté ; panne = concours de la veille gardés (jamais bloquant). Bouton officiel → plateforme
  des Finances (`lien_officiel()` de construire_site.py). Exemple enregistré : `tools/exemples/finances.html` (tests).
