# Alerte Concours Tunisie — تنبيه المناظرات

Site gratuit (en construction) : **tous les concours publics ouverts en Tunisie, dans les 24 gouvernorats**, classés
par **gouvernorat** et par **métier**, avec la date limite et le lien officiel ; puis des **alertes** sur Telegram
(par métier ET par gouvernorat), le **suivi des concours choisis** (candidatures acceptées, convocations, résultats)
et un **entraînement** aux épreuves écrites.

Site indépendant, non officiel : on s'inscrit toujours sur le site officiel du concours.

## Comment ça marche (sans PC)
- `robot/lire_concours.py` lit chaque jour le tableau officiel des concours ouverts (www.concours.gov.tn) et écrit
  `donnees/concours.json` (organisme, grade, nombre de postes, dates, état des résultats, métier, gouvernorat).
- `robot/gouvernorats.py` déduit le gouvernorat du nom de l'organisme (« national » = ouvert à toute la Tunisie).
- Robot GitHub `.github/workflows/maj.yml` : chaque jour, lecture → tests → enregistrement.
- Test : `python tools/test_robot.py` (sans réseau).

## Plan de continuité
Tout est dans ce dépôt et tourne sur GitHub. Les notes de travail détaillées sont dans le fichier `CLAUDE.md`.
