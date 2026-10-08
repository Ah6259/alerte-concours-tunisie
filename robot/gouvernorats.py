"""Gouvernorat d'un concours, déduit du nom de l'organisme (le portail officiel ne le donne pas).
« national » = ministère, office ou société nationale sans lieu précis : le concours est ouvert à toute la Tunisie
(il apparaît sur la page de CHAQUE gouvernorat et dans les alertes de tous les gouvernorats).
Lieux : délégations du référentiel du Registre national des entreprises (delegations_ar.json) + 368 municipalités et
leur wilaya (municipalites_ar.json, d'après la liste « قائمة بلديات تونس » de Wikipédia en arabe, CC BY-SA : noms de
lieux seulement, utilisés en interne pour le classement)."""
import json, os, re

ICI = os.path.dirname(os.path.abspath(__file__))
# (slug, nom FR, nom AR, autres écritures arabes)
GOUVERNORATS = [
    ("tunis", "Tunis", "تونس", []), ("ariana", "Ariana", "أريانة", ["اريانة", "أريانه"]), ("ben-arous", "Ben Arous", "بن عروس", []),
    ("manouba", "La Manouba", "منوبة", ["منوبه"]), ("nabeul", "Nabeul", "نابل", []), ("zaghouan", "Zaghouan", "زغوان", []),
    ("bizerte", "Bizerte", "بنزرت", []), ("beja", "Béja", "باجة", ["باجه"]), ("jendouba", "Jendouba", "جندوبة", ["جندوبه"]),
    ("le-kef", "Le Kef", "الكاف", []), ("siliana", "Siliana", "سليانة", ["سليانه"]), ("sousse", "Sousse", "سوسة", ["سوسه"]),
    ("monastir", "Monastir", "المنستير", []), ("mahdia", "Mahdia", "المهدية", ["المهديه"]), ("sfax", "Sfax", "صفاقس", []),
    ("kairouan", "Kairouan", "القيروان", []), ("kasserine", "Kasserine", "القصرين", []), ("sidi-bouzid", "Sidi Bouzid", "سيدي بوزيد", []),
    ("gabes", "Gabès", "قابس", []), ("medenine", "Médenine", "مدنين", []), ("tataouine", "Tataouine", "تطاوين", []),
    ("gafsa", "Gafsa", "قفصة", ["قفصه"]), ("tozeur", "Tozeur", "توزر", []), ("kebili", "Kébili", "قبلي", []),
]
NATIONAL = ("national", "Toute la Tunisie", "كامل الجمهورية")
REF_RNE = {"Tunis": "tunis", "Ben Arous": "ben-arous", "Ariana": "ariana", "Béja": "beja", "Bizerte": "bizerte", "Gabes": "gabes",
           "Gafsa": "gafsa", "Jendouba": "jendouba", "Kairouan": "kairouan", "Kasserine": "kasserine", "Gbilli": "kebili", "Kef": "le-kef",
           "Mahdia": "mahdia", "Manouba": "manouba", "Mednine": "medenine", "Monastir": "monastir", "Nabeul": "nabeul", "Sfax": "sfax",
           "Sidi Bouzid": "sidi-bouzid", "Siliana": "siliana", "Sousse": "sousse", "Tataouine": "tataouine", "Touzer": "tozeur", "Zaghouan": "zaghouan"}
# noms trop courants pour être un lieu sûrs (ils apparaissent dans d'autres mots ou expressions)
TROP_COURANTS = {"المدينة", "الزهور", "القصر", "العلا", "النصر", "الوسط", "الشمال", "الجنوب", "السلام", "التحرير", "الحرية", "الرياض", "النور"}

LIEUX = []   # (motif compilé, slug), les noms les plus longs d'abord
def _ajoute(nom, slug):
    nom = nom.strip()
    if len(nom) >= 3 and nom not in TROP_COURANTS:
        LIEUX.append((nom, slug))
for slug, fr, ar, autres in GOUVERNORATS:
    for n in [ar] + autres:
        _ajoute(n, slug)
for nom, g in json.load(open(os.path.join(ICI, "delegations_ar.json"), encoding="utf-8")).items():
    if g in REF_RNE:
        _ajoute(nom, REF_RNE[g])
for nom, slug in json.load(open(os.path.join(ICI, "municipalites_ar.json"), encoding="utf-8")).items():
    _ajoute(nom, slug)
LIEUX.sort(key=lambda x: -len(x[0]))
SANS_ESPACE = [(n.replace(" ", ""), slug) for n, slug in LIEUX]
LIEUX = [(re.compile(r"(?:^|[\s\-«(،,]|ب|ل|ال)" + re.escape(n) + r"(?=$|[\s\-»)،,.])"), slug) for n, slug in LIEUX]


def gouvernorat(organisme):
    t = " " + (organisme or "").replace("ـ", "") + " "
    # « تونس » seul dans « البلاد التونسية », « التونسية » … ne désigne pas le gouvernorat de Tunis
    t_sans_pays = re.sub(r"(للبلاد|البلاد|الجمهورية) التونسية|التونسي[ةه]?", " ", t)
    for motif, slug in LIEUX:
        if motif.search(t_sans_pays):
            return slug
    # municipalité écrite sans espace (« بلدية دارعلوش ») : comparaison sans espaces
    m = re.match(r"\s*بلدية\s*(.+?)\s*$", t_sans_pays)
    if m:
        coll = m.group(1).replace(" ", "")
        for nom, slug in SANS_ESPACE:
            if coll == nom:
                return slug
    return NATIONAL[0]


NOMS = {s: (fr, ar) for s, fr, ar, _ in GOUVERNORATS}
NOMS[NATIONAL[0]] = NATIONAL[1:]
