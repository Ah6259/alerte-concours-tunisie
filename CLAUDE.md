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
Construire : `python robot/construire_site.py [--aujourdhui AAAA-MM-JJ]`.
Tests : `python tools/test_robot.py` (29) et `node tools/test_site.mjs` (61, jsdom ; dont les pages des concours, sabotage vérifié) — sabotage vérifié le 08/10 (filtre
national cassé → détecté).

## État au 08/10/2026
Fait : robot, classement métier / gouvernorat, pages FR + AR, tests, publication GitHub Pages.
À faire : portail + vidéo, Search Console, vérification du matin et gendarme IA (ajouter ce dépôt à leurs sources),
actualités du portail et ANETI, puis Alertes / Suivi (Telegram, paiement 3 étapes), puis Entraînement.
