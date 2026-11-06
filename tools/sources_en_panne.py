"""Alerte « source en panne » (15/10/2026, règle commune § 17 : aucun robot vert qui ne fait rien).

Le tableau des concours arrête déjà le robot s'il est illisible. Mais les ACTUALITÉS du portail et la plateforme du
ministère des FINANCES ne bloquent rien (le site doit se mettre à jour quand même) : une panne restait invisible.
Lancé APRÈS l'enregistrement par maj.yml : une source sans lecture réussie depuis plus de JOURS jours -> échec
(GitHub prévient Ahmed par e-mail). Les données des autres sources sont déjà enregistrées.
"""
import datetime as dt
import json
import os
import re
import sys

JOURS = 2
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SOMMEIL AUTOMATIQUE (06/11/2026, règle commune § 55, Ahmed : « si le problème se reproduit, il est réglé automatiquement ») :
# une source dont le SITE refuse la connexion (refus, délai, 403/429/5xx, adresse introuvable : rien à réparer chez nous, jamais
# de contournement) est réessayée à chaque passage et revient seule ; pas d'échec pendant SOMMEIL_MAX_JOURS après sa dernière
# lecture réussie (ligne « SOMMEIL »), puis l'alarme sonne (décider de la retirer). Une erreur de lecture CHEZ NOUS (page
# changée, liste trop courte…) sonne toujours après JOURS jours.
SOMMEIL_MAX_JOURS = 30
EXTERNE = re.compile(r"refused|reset by peer|timed? ?out|Errno (101|104|110|111|113)|HTTP Error (403|429|5\d\d)|injoignable|"
                     r"Temporary failure|Name or service not known|unreachable|No route to host|Cloudflare", re.I)


def en_sommeil(derniere, raison, jour):
    """Date de fin du sommeil si la panne vient du site lui-même et dure depuis moins de SOMMEIL_MAX_JOURS, sinon None."""
    if not derniere or not raison or not EXTERNE.search(raison):
        return None
    fin = (dt.date.fromisoformat(str(derniere)[:10]) + dt.timedelta(days=SOMMEIL_MAX_JOURS)).isoformat()
    return fin if jour <= fin else None


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
    c, auj = lire("concours.json"), dt.date.today().isoformat()
    p = en_panne(c, lire("actualites.json"), auj)
    # 06/11/2026 : plateforme des Finances qui refuse la connexion (raison notée par robot/lire_concours.py) = sommeil
    dors = [x for x in p if x[0] == "plateforme du ministère des Finances" and en_sommeil(x[1], c.get("finances_raison", ""), auj)]
    p = [x for x in p if x not in dors]
    for s, d in dors:
        print(f"SOMMEIL source {s} : son site refuse la connexion depuis le {d} ({c.get('finances_raison')}) — réessayée à chaque passage, "
              f"revient seule ; alarme après le {en_sommeil(d, c.get('finances_raison', ''), auj)} (décider alors de la retirer)")
    for s, d in p:
        print(f"ÉCHEC source {s} : dernière lecture réussie le {d or 'jamais'} — à réparer")
    sys.exit(1 if p else 0)
