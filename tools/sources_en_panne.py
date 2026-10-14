"""Alerte « source en panne » (15/10/2026, règle commune § 17 : aucun robot vert qui ne fait rien).

Le tableau des concours arrête déjà le robot s'il est illisible. Mais les ACTUALITÉS du portail et la plateforme du
ministère des FINANCES ne bloquent rien (le site doit se mettre à jour quand même) : une panne restait invisible.
Lancé APRÈS l'enregistrement par maj.yml : une source sans lecture réussie depuis plus de JOURS jours -> échec
(GitHub prévient Ahmed par e-mail). Les données des autres sources sont déjà enregistrées.
"""
import datetime as dt
import json
import os
import sys

JOURS = 2
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def en_panne(concours, actualites, jour):
    lim = (dt.date.fromisoformat(jour) - dt.timedelta(days=JOURS)).isoformat()
    sources = {"tableau des concours (concours.gov.tn)": concours.get("lu_le"),
               "plateforme du ministère des Finances": concours.get("finances_ok"),
               "actualités du portail (concours.gov.tn)": actualites.get("lu_le")}
    return [(s, d) for s, d in sources.items() if (d or "") < lim]


if __name__ == "__main__":
    for _f in (sys.stdout, sys.stderr):
        if hasattr(_f, "reconfigure"):
            _f.reconfigure(encoding="utf-8", errors="replace")
    lire = lambda n: json.load(open(os.path.join(RACINE, "donnees", n), encoding="utf-8")) if os.path.exists(os.path.join(RACINE, "donnees", n)) else {}
    p = en_panne(lire("concours.json"), lire("actualites.json"), dt.date.today().isoformat())
    for s, d in p:
        print(f"ÉCHEC source {s} : dernière lecture réussie le {d or 'jamais'} — à réparer")
    sys.exit(1 if p else 0)
