// Test du site Alerte Concours Tunisie (à lancer après « python robot/construire_site.py ») :
//   npm install --no-save --no-package-lock jsdom ; node tools/test_site.mjs
import { readFileSync, existsSync, readdirSync, statSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const lire = f => readFileSync(join(root, f), "utf8");
let ok = 0, ko = 0;
const check = (nom, cond) => { if (cond) ok++; else { ko++; console.log("ÉCHEC " + nom); } };

const D = JSON.parse(lire("donnees/concours.json"));
const GOUVS = ["tunis", "ariana", "ben-arous", "manouba", "nabeul", "zaghouan", "bizerte", "beja", "jendouba", "le-kef", "siliana", "sousse",
  "monastir", "mahdia", "sfax", "kairouan", "kasserine", "sidi-bouzid", "gabes", "medenine", "tataouine", "gafsa", "tozeur", "kebili"];
const pages = ["index.html", "actualites/index.html", "guide-inscription/index.html", "alertes/index.html", "alertes/conditions/index.html", "ministeres/index.html", "a-propos/index.html",
  ...GOUVS.map(g => `gouvernorat/${g}/index.html`), "gouvernorat/national/index.html",
  ...readdirSync(join(root, "metier")).map(m => `metier/${m}/index.html`)];

// ---- 0. Lieux (règle commune § 11.11, 18/10/2026) : les gouvernorats proposés = les 24 de La Poste + l'exception listée ici
//      (« national » = toute la Tunisie, un groupe et non un gouvernorat), dans les deux sens : toutes présentes, rien d'autre
{ const OFFICIELS = ["ariana", "beja", "ben arous", "bizerte", "gabes", "gafsa", "jendouba", "kairouan", "kasserine", "kebili", "kef", "mahdia",
    "manouba", "medenine", "monastir", "nabeul", "sfax", "sidi bouzid", "siliana", "sousse", "tataouine", "tozeur", "tunis", "zaghouan"];
  const EXCEPTIONS = ["national"];   // relue à la main
  const norm = s => String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/-/g, " ").replace(/^(la|le) /, "").trim();
  const exact = (l, avec) => { const n = l.map(norm), att = [...OFFICIELS, ...avec];
    return n.length === att.length && new Set(n).size === n.length && att.every(o => n.includes(o)) && n.every(x => att.includes(x)); };
  const accL = lire("index.html");
  const m = accL.match(/<select id="f-gouv"[^>]*>([\s\S]*?)<\/select>/);
  const vals = m ? [...m[1].matchAll(/<option value="([^"]*)"/g)].map(o => o[1]).filter(Boolean) : [];
  check("lieux : liste « Gouvernorat » de l'accueil = les 24 gouvernorats officiels + « national », rien d'autre", exact(vals, EXCEPTIONS));
  check("lieux : pages de gouvernorat = les 24 officiels + « national », rien d'autre",
    exact(readdirSync(join(root, "gouvernorat")).filter(n => existsSync(join(root, "gouvernorat", n, "index.html"))), EXCEPTIONS));
  check("lieux : carte de l'accueil = une bulle par gouvernorat officiel, rien d'autre", exact([...accL.matchAll(/class="tn-b[^"]*" data-gouv="([^"]+)"/g)].map(x => x[1]), []));
  check("lieux : chaque concours est rangé dans un gouvernorat officiel ou « national »", D.concours.every(c => OFFICIELS.includes(norm(c.gouvernorat)) || EXCEPTIONS.includes(c.gouvernorat))); }

// ---- 1. Données
check("données : au moins 20 concours lus, chacun avec organisme, grade, métier et gouvernorat", D.concours.length >= 20
  && D.concours.every(c => c.organisme && c.grade && c.metier && c.gouvernorat));
check("données : au moins un concours local (gouvernorat) et un national", D.concours.some(c => c.gouvernorat === "national") && D.concours.some(c => GOUVS.includes(c.gouvernorat)));

// ---- 2. Pages : toutes présentes, propres, FR + AR
check("pages : accueil, 24 gouvernorats + national, métiers, guide, alertes, à propos", pages.every(p => existsSync(join(root, p))) && pages.length >= 38);
for (const p of pages) {
  const h = lire(p);
  const ok1 = /<title>[^<]{10,}<\/title>/.test(h) && /name="description" content="[^"]{30,}"/.test(h) && /rel="canonical" href="https:\/\/concours\.clicvia\.com\//.test(h)
    && h.includes('http-equiv="Content-Security-Policy"') && /content="(noindex, follow, )?noai, noimageai"/.test(h) && h.includes('data-l="ar"') && h.includes("assets/page.js")
    && !/undefined|NaN|\[object/.test(h) && !/<script>(?!\s*$)/.test(h.replace(/<script type="application\/ld\+json">[\s\S]*?<\/script>/g, ""));
  check(`${p} : titre, description, adresse canonique, sécurité, français + arabe, aucun trou`, ok1);
}
const acc = lire("index.html");
check("accueil : formulaire « Votre avis » et lien vers le guide d'inscription", acc.includes('id="avis-form"') && acc.includes('href="guide-inscription/"'));
check("cartes : lien vers le portail officiel (https) pour s'inscrire", (acc.match(/class="officiel" href="https:\/\/www\.concours\.gov\.tn\//g) || []).length >= 10);
check("accueil : toutes les cartes des concours ouverts", (acc.match(/<article class="ao/g) || []).length === D.concours.filter(c => !c.cloture_candidatures || c.cloture_candidatures >= (D.lu_le || "")).length);
// un concours national apparaît dans CHAQUE gouvernorat
const nat = D.concours.find(c => c.gouvernorat === "national" && (!c.cloture_candidatures || c.cloture_candidatures >= D.lu_le));
check("un concours national figure sur la page de chaque gouvernorat (demande d'Ahmed)", !nat || GOUVS.every(g => lire(`gouvernorat/${g}/index.html`).includes(`id="c-${nat.id}"`)));
const loc = D.concours.find(c => c.gouvernorat !== "national" && (!c.cloture_candidatures || c.cloture_candidatures >= D.lu_le));
check("un concours local figure seulement dans son gouvernorat", !loc || (lire(`gouvernorat/${loc.gouvernorat}/index.html`).includes(`id="c-${loc.id}"`)
  && GOUVS.filter(g => g !== loc.gouvernorat).every(g => !lire(`gouvernorat/${g}/index.html`).includes(`id="c-${loc.id}"`))));

// ---- 3. Google, robots, téléphone
// une page par concours (08/10/2026) : chaque concours du tableau officiel, avec grade, organisme, lien officiel, guide, canonique
const pc = D.concours.map(c => [c, `concours/${c.id}/index.html`]);
check(`pages des concours : une par concours (${D.concours.length}), grade + organisme, lien officiel https, guide, adresse canonique`,
  pc.every(([c, f]) => existsSync(join(root, f)) && (h => h.includes(`<link rel="canonical" href="https://concours.clicvia.com/concours/${c.id}/">`)
    && h.includes(c.source === "finances" ? 'class="officiel" href="https://concours.finances.gov.tn/' : 'class="officiel" href="https://www.concours.gov.tn/') && h.includes('href="../../guide-inscription/"')
    && h.includes(c.grade.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;")) && !/undefined|NaN|None/.test(h))(lire(f))));
const cf = D.concours.filter(c => c.source === "finances");
check("2e source (ministère des Finances) : numéros 900000+, classés « national », lien vers concours.finances.gov.tn, source citée dans le pied de page",
  cf.every(c => +c.id >= 900000 && c.gouvernorat === "national" && /^https:\/\/concours\.finances\.gov\.tn\//.test(c.lien)) && acc.includes("concours.finances.gov.tn")
  && D.concours.filter(c => c.source !== "finances").every(c => +c.id < 900000));
check("cartes : le grade mène à la page du concours", D.concours.filter(c => acc.includes(`id="c-${c.id}"`)).every(c => acc.includes(`href="concours/${c.id}/"`)) && acc.includes('href="concours/'));
// carte de la Tunisie (08/10/2026, comme les autres sites) : 24 bulles cliquables sur l'accueil ; sur une page de gouvernorat, la sienne en surbrillance
const bullesAcc = [...acc.matchAll(/<a href="gouvernorat\/([a-z-]+)\/" class="tn-b[^"]*" data-gouv="([a-z-]+)"/g)];
check("carte de la Tunisie EN HAUT (bandeau) de l'accueil et des pages de gouvernorat, avant la liste (règle d'Ahmed)", /<section class="hero">[\s\S]*class="hero-carte"[\s\S]*<\/section>\s*<main/.test(acc) && acc.indexOf('class="hero-carte"') < acc.indexOf('id="liste"')
  && GOUVS.every(g => (h => h.indexOf('class="hero-carte petite"') > 0 && h.indexOf('class="hero-carte petite"') < h.indexOf('id="liste"'))(lire(`gouvernorat/${g}/index.html`))));
check("carte de la Tunisie : 24 gouvernorats sur l'accueil, chaque bulle mène à sa page", bullesAcc.length === 24 && bullesAcc.every(m => m[1] === m[2] && GOUVS.includes(m[1])));
check("carte de la Tunisie : nombres recalculés par le navigateur seulement sur l'accueil (sinon 0 partout sur une page de gouvernorat)", /if \(document\.getElementById\("f-gouv"\)\) document\.querySelectorAll\("\.tn-b\[data-gouv\] text"\)/.test(lire("assets/app.js")));
{ const ouv = D.concours.filter(c => !c.cloture_candidatures || c.cloture_candidatures >= D.lu_le), nNat = ouv.filter(c => c.gouvernorat === "national").length;
  const chiffre = g => +((acc.match(new RegExp(`data-gouv="${g}"><title>[^<]*</title><circle[^>]*/><text[^>]*>(\\d+)</text>`)) || [])[1] ?? -1);
  check("carte de la Tunisie : chaque bulle = concours du gouvernorat + nationaux (aucun gouvernorat à 0 s'il y a des nationaux), légende claire",
    GOUVS.every(g => chiffre(g) === ouv.filter(c => c.gouvernorat === g).length + nNat) && acc.includes("concours nationaux, ouverts partout")
    && /c\.dataset\.gouv === t\.parentNode\.dataset\.gouv \|\| c\.dataset\.gouv === "national"/.test(lire("assets/app.js"))); }
check("carte de la Tunisie : sur chaque page de gouvernorat, sa bulle est en surbrillance", GOUVS.every(g => new RegExp(`class="tn-b[^"]*actif" data-gouv="${g}"`).test(lire(`gouvernorat/${g}/index.html`))));
// actualités du portail (08/10/2026) : page « actualites/ » + 4 dernières sur l'accueil, chacune avec son lien officiel
const AC = existsSync(join(root, "donnees/actualites.json")) ? JSON.parse(lire("donnees/actualites.json")).actualites : [];
if (AC.length) {
  const pa = lire("actualites/index.html");
  check(`actualités : page avec les ${AC.length} avis, chacun avec son lien officiel https vers SON avis`, (pa.match(/<article class="actu /g) || []).length === AC.length
    && AC.every(x => pa.includes(`href="${x.lien}"`) && /^https:\/\/www\.concours\.gov\.tn\/P1\/index31\.aspx\?id=\d+$/.test(x.lien)));
  check("actualités : résumés courts seulement (300 caractères au plus)", AC.every(x => x.resume.length <= 301));
  check("accueil : les 4 dernières actualités + lien vers la page", (acc.match(/<article class="actu /g) || []).length === Math.min(4, AC.length) && acc.includes('href="actualites/"'));
}
const sm = lire("sitemap.xml");
check("plan du site : les pages des concours", D.concours.every(c => sm.includes(`https://concours.clicvia.com/concours/${c.id}/`)));
const indexees = pages.filter(p => !lire(p).includes('content="noindex'));
check("plan du site : toutes les pages indexables", indexees.every(p => sm.includes("https://concours.clicvia.com/" + p.replace(/index\.html$/, ""))));
// VS.4 (18/10/2026) : page métier sans concours ouvert -> message utile (alerte, tous les concours), « noindex », hors du plan du site ; jamais « 0 concours ouvert »
{
  const ouvM = D.concours.filter(c => !c.cloture_candidatures || c.cloture_candidatures >= (D.lu_le || ""));
  const metiers = readdirSync(join(root, "metier"));
  const vides = metiers.filter(m => !ouvM.some(c => c.metier === m)), pleins = metiers.filter(m => ouvM.some(c => c.metier === m));
  check(`métiers vides (${vides.join(", ") || "aucun aujourd'hui"}) : noindex, absents du plan du site, message utile avec lien Alertes + tous les concours, pas de « 0 concours »`,
    vides.every(m => { const h = lire(`metier/${m}/index.html`);
      return h.includes('content="noindex, follow, noai, noimageai"') && !sm.includes(`/metier/${m}/</loc>`) && h.includes('id="metier-vide"')
        && h.includes('id="vide-alertes" href="../../alertes/"') && h.includes('id="vide-tous" href="../../#liste"') && !/>\s*0 concours/.test(h) && !h.includes('id="compte"'); }));
  check("métiers avec des concours ouverts : indexés, dans le plan du site, sans message « aucun »", pleins.length > 0
    && pleins.every(m => { const h = lire(`metier/${m}/index.html`); return h.includes('content="noai, noimageai"') && sm.includes(`/metier/${m}/</loc>`) && !h.includes('id="metier-vide"') && h.includes('id="compte"'); }));
  check("aucune page du site n'annonce « 0 concours ouvert(s) »", pages.every(p => !/>\s*0 concours ouverts?\b/.test(lire(p))));
}
const rb = lire("robots.txt");
check("robots.txt : Google autorisé, robots d'IA refusés, plan du site", /User-agent: Googlebot\nAllow: \//.test(rb) && /User-agent: GPTBot\nDisallow: \//.test(rb) && /User-agent: ClaudeBot\nDisallow: \//.test(rb) && rb.includes("sitemap.xml"));
const man = JSON.parse(lire("manifest.webmanifest"));
check("manifeste : id propre au site, icônes présentes", man.id === "/" && man.icons.every(i => existsSync(join(root, i.src))));
check("image d'aperçu WhatsApp et icônes", existsSync(join(root, "assets/og-image-v2.jpg")) && statSync(join(root, "assets/og-image-v2.jpg")).size < 250 * 1024 && lire("index.html").includes("assets/og-image-v2.jpg") && lire("index.html").includes('og:image:type" content="image/jpeg"')
  && existsSync(join(root, "assets/apple-touch-icon.png")) && existsSync(join(root, "favicon.ico")) && existsSync(join(root, "assets/logo.svg")));
check("service worker propre au site", /const PREFIXE = "alerte-concours-tunisie-"/.test(lire("sw.js")) && lire("assets/page.js").includes('register(BASE_SITE + "sw.js"'));
// jamais le nom d'un site concurrent dans le dépôt public (noms écrits à l'envers ici)
const interdits = ["moc.einisutsruocnoc", "nt.sruocnoceinisut"].map(x => [...x].reverse().join(""));
const tous = []; (function parcourir(d) { for (const f of readdirSync(d)) { const c = join(d, f); if (f === "node_modules" || f === ".git") continue; statSync(c).isDirectory() ? parcourir(c) : /\.(html|js|mjs|py|md|json|txt|xml|css)$/.test(f) && tous.push(c); } })(root);
check("aucun nom de site concurrent dans le dépôt public", tous.every(f => interdits.every(n => !readFileSync(f, "utf8").toLowerCase().includes(n))));

// ---- 4. Comme dans un navigateur : filtres (un concours national reste visible quel que soit le gouvernorat)
let JSDOM = null;
try { ({ JSDOM } = await import("jsdom")); } catch (e) { console.log("(jsdom absent : tests du navigateur ignorés)"); }
if (JSDOM) {
  const html = acc.replace(/<script[^>]*src="[^"]*"[^>]*><\/script>/g, "");
  const dom = new JSDOM(html, { runScripts: "outside-only", url: "https://concours.clicvia.com/?jour=" + D.lu_le, pretendToBeVisual: true });
  const w = dom.window; w.localStorage.setItem("langue", "fr");
  for (const js of ["assets/page.js", "assets/son.js", "assets/app.js"]) w.eval(lire(js));
  w.document.dispatchEvent(new w.Event("DOMContentLoaded"));
  await new Promise(r => setTimeout(r, 30));
  const d = w.document, ouvertes = () => [...d.querySelectorAll("#liste .ao")].filter(c => c.dataset.ok === "1");
  check("navigateur : en-tête fabriqué (nom du site, bouton langue)", d.getElementById("entete").textContent.includes("Alerte Concours") && !!d.querySelector(".langue"));
  const total = ouvertes().length;
  const g = (loc || {}).gouvernorat || "tunis";
  const fg = d.getElementById("f-gouv"); fg.value = g; fg.dispatchEvent(new w.Event("change"));
  const vis = ouvertes();
  check(`navigateur : filtre gouvernorat « ${g} » → ses concours + les concours nationaux`, vis.length > 0 && vis.length < total && vis.every(c => c.dataset.gouv === g || c.dataset.gouv === "national")
    && (!nat || vis.some(c => c.dataset.gouv === "national")));
  check("navigateur : la carte suit le filtre — le gouvernorat choisi, et lui seul, est entouré sur la carte (règle § 11.11)",
    (a => g === "national" ? a.length === 0 : a.length === 1 && a[0].dataset.gouv === g)([...d.querySelectorAll(".carte-tn .tn-b.actif")]));
  fg.value = ""; fg.dispatchEvent(new w.Event("change"));
  const fq = d.getElementById("f-q"); fq.value = "zzzzqqq"; fq.dispatchEvent(new w.Event("input"));
  check("navigateur : recherche sans résultat → message « Aucun concours »", ouvertes().length === 0 && !d.getElementById("vide").hidden);
  // Recherche « au son » (règle commune § 27, 18/10/2026, demande d'Ahmed) : deux écritures d'un même nom = même résultat
  { const S = w.sonRecherche, chercher = t => { fq.value = t; fq.dispatchEvent(new w.Event("input")); return ouvertes().map(c => c.id); };
    const commun = join(root, "..", "projets-ahmed", "outils communs", "recherche-au-son", "son.js");
    check("recherche au son : assets/son.js chargé avant app.js sur toutes les pages (copie identique de l'outil commun quand il est présent)", !!S
      && /assets\/son\.js\?v=[^"]+"><\/script>\s*<script src="[^"]*assets\/app\.js/.test(acc) && (!existsSync(commun) || readFileSync(commun, "utf8") === lire("assets/son.js")));
    const paires = [["Djerba", "Jerba"], ["Kairouan", "Qairouan"], ["Hammamet", "Hamamet"], ["Houmt Souk", "Houmet Essouk"]];
    check("recherche au son : Djerba = Jerba, Kairouan = Qairouan, Hammamet = Hamamet, Houmt Souk = Houmet Essouk (même résultat)",
      paires.every(([a, b]) => chercher(a).join() === chercher(b).join()) &&
      paires.every(([a, b]) => S.trouve(S.cle("Commune de " + a), b) && S.trouve(S.cle("Commune de " + b), a)));
    // une paire tirée des VRAIS concours : un mot d'un titre écrit avec une consonne doublée
    const mots = [...d.querySelectorAll("#liste .ao")].flatMap(c => ((c._q || c.textContent.toLowerCase()).match(/\b[a-z]{6,}\b/g) || []).map(m => [m, c.id]));
    const [mot, id] = mots.find(([m]) => /(?<=[a-z])[aeiou][bcdfglmnprstv][aeiou]/.test(m)) || ["", ""];
    const double = mot.replace(/(?<=[a-z])([aeiou])([bcdfglmnprstv])(?=[aeiou])/, "$1$2$2");
  const triple = mot.replace(/(?<=[a-z])([aeiou])([bcdfglmnprstv])(?=[aeiou])/, "$1$2$2$2");   // lettre triplée (« demisssion ») ; jamais au début du mot : « ettudes » y serait lu comme l'article (« Ettadhamen » = « Tadhamen »)
    const r1 = chercher(mot), r2 = chercher(double);
    check(`recherche au son : « ${mot} » écrit « ${double} » ou « ${triple} » trouve les mêmes concours ; « demisssion » = « Démission »`, !!mot && r2.includes(id) && r2.every(x => r1.includes(x))
    && chercher(triple).join() === r2.join() && S.trouve(S.cle("Démission"), "demisssion"));
    check("recherche au son : une recherche absurde (« zzzzqqq ») ne trouve toujours rien", chercher("zzzzqqq").length === 0);
    chercher(""); }
  d.querySelector(".langue").dispatchEvent(new w.Event("click"));
  check("navigateur : bouton langue → page en arabe (de droite à gauche)", d.documentElement.lang === "ar" && d.documentElement.dir === "rtl");
}

// ---- veille des sites des ministères (08/10/2026)
{ const DM = existsSync(join(root, "donnees/ministeres.json")) ? JSON.parse(lire("donnees/ministeres.json")) : { annonces: [] };
  const pm = lire("ministeres/index.html"), nbm = (pm.match(/<li class="annonce-min">/g) || []).length;
  check("page « sites des ministères » : annonces avec lien officiel (https/http), source citée, lien depuis l'accueil et les actualités",
    nbm >= Math.min(1, DM.annonces.length) && [...pm.matchAll(/<li class="annonce-min">(.*?)<\/li>/g)].every(m => /href="https?:\/\//.test(m[1])) && pm.includes("Source : site officiel")
    && acc.includes('href="ministeres/"') && lire("actualites/index.html").includes('href="../ministeres/"') && sm.includes("ministeres/</loc>")); }
// ---- Alertes concours (abonnement Telegram, 08/10/2026) : page, paiement, formulaire, rien de privé dans ce dépôt
const al = lire("alertes/index.html");
check("alertes : prix 15 DT / 3 mois ou 39 DT / an, pas de renouvellement automatique, alertes dès réception du paiement",
  /15 DT \/ 3 mois/.test(al) && /39 DT \/ an/.test(al) && /Pas de renouvellement automatique/.test(al) && /dès réception du paiement/.test(al));
{ // 20/10/2026 (décision d'Ahmed : « Enlève tous les essais gratuits ») : aucune page, aucun script ni le manifeste ne parle d'essai gratuit
  const fichiers = []; (function parcourir(d) { for (const f of readdirSync(d)) { const c = join(d, f); if (f === "node_modules" || f === ".git" || f === "tools") continue;
    statSync(c).isDirectory() ? parcourir(c) : /\.(html|js|json|webmanifest|txt|xml)$/.test(f) && fichiers.push(c); } })(root);
  const ESSAI = /essais? gratuits?|jours? d(?:'|&#x27;|&#39;|’)essai|(?:votre|pendant l(?:'|&#x27;|&#39;|’)|après l(?:'|&#x27;|&#39;|’)|fin de l(?:'|&#x27;|&#39;|’))essai\b|free[ -]trial|trial (?:until|period)|تجربة مجانية|التجربة المجانية|تجربتك|بعد التجربة|نهاية التجربة/i;
  const fautifs = fichiers.filter(c => ESSAI.test(readFileSync(c, "utf8"))).map(c => c.slice(root.length + 1));
  check(`aucune page ne parle d'essai gratuit / free trial / تجربة مجانية (${fichiers.length} fichiers lus)` + (fautifs.length ? " : " + fautifs.slice(0, 5).join(", ") : ""),
    fichiers.length > 100 && !fautifs.length);
  check("formulaire : plus de formule « essai » (3 mois cochés par défaut)", !/value="essai/.test(al) && /name="formule" value="3 mois" checked/.test(al)); }
check("alertes : paiement en 3 étapes D17 / IZI au 24 321 390 (logos, écrans d'exemple), phrase de confiance, preuve WhatsApp",
  /<ol class="paie-etapes">/.test(al) && /class="paie-confiance"/.test(al) && al.includes("24 321 390") && /href="https:\/\/wa\.me\/21624321390\?text=/.test(al)
  && ["d17.png", "izi.png", "transfert-d17.svg", "transfert-izi.svg"].every(f => existsSync(join(root, "assets/paiement", f))) && /src="\.\.\/assets\/paiement\/d17\.png"/.test(al));
check("alertes : formulaire Formspree (mwlpakqj) : nom, téléphone, métiers, gouvernorats (+ « Toute la Tunisie »), concours à suivre, formule, conditions",
  /<form id="abo-form" action="https:\/\/formspree\.io\/f\/mwlpakqj"/.test(al) && /name="nom" required/.test(al) && /name="telephone" required/.test(al)
  && (al.match(/name="metiers"/g) || []).length >= 10 && (al.match(/name="gouvernorats"/g) || []).length === 25 && /id="g-tous"/.test(al)
  && /name="suivis"/.test(al) && (al.match(/name="formule"/g) || []).length === 2 && /href="conditions\/"/.test(al));
check("alertes : script externe abonnement.js sur cette page seulement", /<script src="\.\.\/assets\/abonnement\.js\?v=/.test(al) && !/abonnement\.js/.test(acc));
{ // 18/10/2026 : le motif du paiement est le CODE PERSONNEL donné à l'inscription (#abo-code) — jamais « votre nom » / « nom de l'entreprise » ailleurs sur la page ou dans les conditions
  const sansBalises = f => lire(f).replace(/<[^>]*>/g, " ");
  const contradictions = [/pour motif (votre nom|le nom)/, /name as reference/, /motif du paiement et facture/];
  check("paiement : motif = code personnel partout (page d'abonnement + conditions), aucune phrase « motif = nom »",
    /id="abo-code"/.test(lire("alertes/index.html")) && /motif[^.]{0,40}code personnel/.test(sansBalises("alertes/index.html")) && /code personnel/.test(sansBalises("alertes/conditions/index.html")) &&
    ["alertes/index.html", "alertes/conditions/index.html"].every(f => contradictions.every(r => !r.test(sansBalises(f)))));
}
const co = lire("alertes/conditions/index.html");
check("conditions : prix, paiement, arrêt (/stop), données personnelles, non officiel", /15 DT pour 3 mois/.test(co) && /\/stop/.test(co) && /Données personnelles/.test(co) && /pas officiel/.test(co));
check("accueil + pages : gros bouton doré vers alertes/ (avec le prix)", /class="btn-pro-grand" id="btn-alertes" href="alertes\/"/.test(acc) && /15 DT \/ 3 mois/.test(acc)
  && /class="btn-pro-grand" id="btn-alertes" href="\.\.\/\.\.\/alertes\/"/.test(lire(`gouvernorat/${GOUVS[0]}/index.html`)));
check("sitemap : alertes/ et alertes/conditions/", sm.includes("alertes/</loc>") && sm.includes("alertes/conditions/</loc>"));
check("aucune donnée d'abonné dans ce dépôt public (abonnes.json, chat_id, jeton Telegram)",
  !existsSync(join(root, "abonnes.json")) && !existsSync(join(root, "donnees/abonnes.json")) && !/chat_id|bot\d{6,}:/.test(al + lire("assets/abonnement.js")));
if (JSDOM) {
  const envois = [];
  const dom = new JSDOM(al, { runScripts: "outside-only", url: "https://concours.clicvia.com/alertes/", pretendToBeVisual: true });
  const w = dom.window, d = w.document;
  w.fetch = (url, o) => { envois.push([url, o.body]); return Promise.resolve({ ok: true }); };
  w.eval(lire("assets/page.js")); w.eval(lire("assets/abonnement.js"));
  d.dispatchEvent(new w.Event("DOMContentLoaded"));
  const f = d.getElementById("abo-form"), caseG = v => d.querySelector(`#abo-gouv input[value="${v}"]`);
  const soumettre = async () => { f.dispatchEvent(new w.Event("submit", { cancelable: true })); await new Promise(r => setTimeout(r, 20)); };
  caseG("sfax").checked = true; caseG("sfax").dispatchEvent(new w.Event("change", { bubbles: true }));
  caseG("tous").checked = true; caseG("tous").dispatchEvent(new w.Event("change", { bubbles: true }));
  check("alertes : « Toute la Tunisie » décoche les gouvernorats", caseG("tous").checked && !caseG("sfax").checked);
  f.querySelector('[name="nom"]').value = "Test Candidat"; f.querySelector('[name="telephone"]').value = "24 321 390";
  await soumettre();
  check("alertes : sans métier coché → message d'erreur, rien n'est envoyé", envois.length === 0 && /métier/.test(d.getElementById("abo-status").textContent));
  f.querySelector('#abo-metiers input').checked = true; f.querySelector('[name="suivis"]').value = "n° 2390 ; 2412, abc";
  await soumettre();
  check("alertes : conditions non acceptées → rien n'est envoyé", envois.length === 0 && /conditions/.test(d.getElementById("abo-status").textContent));
  d.getElementById("abo-conditions").checked = true;
  await soumettre();
  const corps = envois[0] && envois[0][1];
  check("alertes : envoi à Formspree avec la ligne « pour_activer » (téléphone 8 chiffres, concours suivis nettoyés), puis confirmation",
    envois.length === 1 && /formspree\.io\/f\/mwlpakqj/.test(envois[0][0]) && corps.get("telephone") === "24321390" && corps.get("suivis") === "2390, 2412"
    && /suivis: 2390,2412/.test(corps.get("pour_activer")) && f.hidden && !d.getElementById("apres-abo").hidden
    && /Test%20Candidat/.test(d.getElementById("abo-preuve-apres").getAttribute("href")));
  // 14/10/2026 (règle commune § 15 : inscription immédiate ; plus d'essai depuis le 20/10/2026) : code créé sur place, lien Telegram avec les choix, gestes expliqués avant
  const code = d.getElementById("abo-code").textContent, lienTg = d.getElementById("abo-ouvrir-tg").getAttribute("href");
  const mSorted = f.getAttribute("data-metiers").split(","), premier = f.querySelector('#abo-metiers input').value;
  check("inscription immédiate : code de 6 caractères affiché, « Ouvrir Telegram » avec les choix (start=e<CODE>_<métiers>_x), code envoyé à Formspree et dans WhatsApp",
    /^[A-HJ-NP-Z2-9]{6}$/.test(code) && lienTg === `https://t.me/AlerteConcoursTunisieBot?start=e${code}_${w.ESSAI_ALERTES.encoder([premier], mSorted)}_x`
    && lienTg.split("start=")[1].length <= 64 && corps.get("code") === code && /code%20/.test(d.getElementById("abo-preuve-apres").getAttribute("href")));
  check("inscription immédiate : 3 gestes expliqués avant Telegram (DÉMARRER, réponse le matin suivant vers 8 h) ; plus d'« activation sous 24 heures »",
    d.querySelectorAll("#apres-abo .etapes-tg li").length === 3 && /DÉMARRER/.test(d.getElementById("apres-abo").textContent)
    && /le matin suivant, vers 8 h/.test(d.getElementById("apres-abo").textContent) && !/24 heures/.test(al));
  check("inscription immédiate : listes triées du formulaire = cases du formulaire", JSON.stringify([...f.querySelectorAll('#abo-metiers input')].map(x => x.value).sort()) === JSON.stringify(mSorted));
}

// 15/10/2026 (demande d'Ahmed) : « Votre avis » = e-mail obligatoire + confirmation bien visible dans la carte
check("Votre avis : e-mail obligatoire (required, « obligatoire ») et confirmation « Merci ! Votre avis a bien été envoyé » dans la carte",
  /id="avis-email" name="email" autocomplete="email" required/.test(acc) && /obligatoire, pour vous répondre/.test(acc)
  && /avis-merci/.test(lire("assets/avis.js")) && /Merci ! Votre avis a bien été envoyé/.test(lire("assets/avis.js")) && /\[\^\\s@\]\+@/.test(lire("assets/avis.js")));
// ---- Rapports du mois (18/10/2026, règle commune § 25) : chiffres = données du site, mois fini figé, plan du site
{ const H = existsSync(join(root, "donnees/rapports.json")) ? JSON.parse(lire("donnees/rapports.json")).mois : {};
  const mois = Object.keys(H).sort();
  check("rapports : historique présent, au moins le mois des données", mois.length >= 1 && !!H[(D.lu_le || "").slice(0, 7)]);
  const pr = ["rapports/index.html", ...mois.map(m => `rapports/${m}/index.html`)];
  check("rapports : rapports/ et une page par mois, propres (titre, description, canonique, CSP, FR + AR, aucun trou, pas de script en ligne)", pr.every(p => existsSync(join(root, p)) && (h =>
    /<title>[^<]{10,}<\/title>/.test(h) && /name="description" content="[^"]{30,}"/.test(h) && h.includes(`<link rel="canonical" href="https://concours.clicvia.com/${p.replace(/index\.html$/, "")}">`)
    && h.includes('http-equiv="Content-Security-Policy"') && h.includes('data-l="ar"') && !/undefined|NaN|None|\[object/.test(h) && !/ on[a-z]+="/.test(h)
    && !/<script>(?!\s*$)/.test(h.replace(/<script type="application\/ld\+json">[\s\S]*?<\/script>/g, "")))(lire(p))));
  check("rapports : JSON-LD Article + FAQ + fil d'Ariane, méthode et « Citer ces chiffres » sur chaque mois", mois.every(m => (h => h.includes('"@type": "Article"') && h.includes('"@type": "FAQPage"')
    && h.includes('"@type": "BreadcrumbList"') && h.includes('id="methode"') && h.includes('id="citer"'))(lire(`rapports/${m}/index.html`))));
  check("rapports : dans le plan du site avec la date de leurs chiffres", sm.includes("<loc>https://concours.clicvia.com/rapports/</loc>")
    && mois.every(m => sm.includes(`<loc>https://concours.clicvia.com/rapports/${m}/</loc><lastmod>${H[m].dernier_jour}</lastmod>`)));
  check("rapports : lien dans le pied de page (toutes les pages) et sur l'accueil", lire("assets/page.js").includes('href="${racine}rapports/"') && acc.includes('href="rapports/"'));
  check("rapports : 1er mois = « Premier rapport » sans évolution ; mois suivants = évolution", mois.every((m, i) => (h => i === 0 ? h.includes("Premier rapport") && !h.includes('id="evolution"')
    : h.includes('id="evolution"') && !h.includes("Premier rapport"))(lire(`rapports/${m}/index.html`))));
  check("rapports : un mois fini dit « figés » avec sa dernière date ; seul le dernier mois peut être en cours", mois.every((m, i) => (h => H[m].fini
    ? h.includes("figés") && h.includes(`au ${H[m].dernier_jour.split("-").reverse().join("/")}`) && !H[m].vus : i === mois.length - 1 && h.includes("mois en cours"))(lire(`rapports/${m}/index.html`))));
  // chiffres du mois en cours = données du site (même jour) = accueil
  const m = (D.lu_le || "").slice(0, 7), e = H[m];
  if (e && e.dernier_jour === D.lu_le) {
    const ouv = D.concours.filter(c => !c.cloture_candidatures || c.cloture_candidatures >= D.lu_le), somme = cs => cs.reduce((a, c) => a + (c.postes || 0), 0);
    const h = lire(`rapports/${m}/index.html`), nb = id => +((h.match(new RegExp(`id="${id}">([\\d ]+)<`)) || [])[1] || "-1").replace(/ /g, "");
    const fr = n => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
    check(`rapports : concours ouverts (${ouv.length}) et postes (${somme(ouv)}) = données du site et accueil`, nb("rap-ouverts") === ouv.length && nb("rap-postes") === somme(ouv)
      && acc.includes(`<div class="r-ouverts" id="r-ouverts"><b>${ouv.length}</b>`) && acc.includes(`${fr(somme(ouv))} postes à pourvoir en tout`));
    const nat = ouv.filter(c => c.gouvernorat === "national");
    check("rapports : nationaux / locaux = données", nb("rap-nationaux") === nat.length && nb("rap-locaux") === ouv.length - nat.length);
    const lignesG = [...h.matchAll(/<tr data-gouv="([a-z-]+)" data-n="(\d+)" data-postes="(\d+)">/g)];
    check("rapports : chaque ligne par gouvernorat = concours ouverts de ce gouvernorat (et nationaux), aucun gouvernorat oublié",
      lignesG.every(([, g, n, p]) => (cs => cs.length === +n && somme(cs) === +p)(ouv.filter(c => c.gouvernorat === g)))
      && new Set(lignesG.map(x => x[1])).size === new Set(ouv.map(c => c.gouvernorat)).size);
    const lignesM = [...h.matchAll(/<tr data-metier="([a-z-]+)" data-n="(\d+)" data-postes="(\d+)">/g)];
    check("rapports : chaque ligne par métier = concours ouverts de ce métier", lignesM.length === new Set(ouv.map(c => c.metier)).size
      && lignesM.every(([, mt, n, p]) => (cs => cs.length === +n && somme(cs) === +p)(ouv.filter(c => c.metier === mt))));
    const urg = ouv.filter(c => c.cloture_candidatures && (new Date(c.cloture_candidatures) - new Date(D.lu_le)) / 864e5 < 7).length;
    check("rapports : clôturent sous 7 jours = accueil", nb("rap-semaine") === urg && acc.includes(`<div class="r-urgent" id="r-urgent"><b>${urg}</b>`));
    const orgs = {}; ouv.forEach(c => orgs[c.organisme] = (orgs[c.organisme] || 0) + 1);
    const nOrg = Object.values(orgs).filter(n => n >= 3).length;
    check("rapports : organismes classés seulement avec au moins 3 concours, et seulement s'il y en a au moins 3", nOrg >= 3 ? (h.match(/<tr data-n="\d+"><th scope="row" dir="rtl"/g) || []).length === nOrg : !h.includes('id="organismes"'));
  }
}
// ---- Rapports du mois : UN SEUL bouton « Partager ce rapport » en haut et en bas, signature, aperçu de partage (18/10/2026)
{ const H = existsSync(join(root, "donnees/rapports.json")) ? JSON.parse(lire("donnees/rapports.json")).mois : {};
  const pr = [["rapports/index.html", "rapports/"], ...Object.keys(H).sort().map(m => [`rapports/${m}/index.html`, `rapports/${m}/`])];
  for (const [f, c] of pr) {
    const h = lire(f), url = "https://concours.clicvia.com/" + c;
    const bt = [...h.matchAll(/<button class="rap-partager" type="button" data-partage-rapport data-url="([^"]+)" data-titre="([^"]+)" data-texte="([^"]+)"/g)];
    const iH = h.indexOf("rap-partage-haut"), i1 = h.indexOf("<section", h.indexOf("<main")), iB = h.lastIndexOf("data-partage-rapport"), iC = h.lastIndexOf("</section>", h.indexOf("</main>"));
    check(`${c} : 2 boutons « Partager ce rapport » (haut + bas) avec la bonne adresse`, bt.length === 2 && bt.every(m => m[1] === url) && (h.match(/Partager ce rapport/g) || []).length === 2
      && iH > h.indexOf("<main") && iH < i1 && iB > iC);
    check(`${c} : le texte partagé dit de quel site vient l'article`, bt.every(m => m[3].startsWith(m[2] + " — Rapport du mois d’Alerte Concours Tunisie :") && !/clicvia|https?:/.test(m[3])));
    check(`${c} : plus de phrase d'aide sous le bouton (demande d'Ahmed) et zone « Lien copié »`, (h.match(/le menu de votre téléphone s’ouvre/g) || []).length === 0
      && (h.match(/تُفتح قائمة المشاركة في هاتفك/g) || []).length === 0 && (h.match(/class="rap-partage-ok" role="status"/g) || []).length === 2);
    check(`${c} : aucun bouton séparé Facebook / WhatsApp / LinkedIn`, !/facebook\.com\/sharer|wa\.me\/|api\.whatsapp|linkedin\.com\/share|twitter\.com\/intent/.test(h));
    check(`${c} : signature « Un rapport d’Alerte Concours Tunisie · concours.clicvia.com » sous le titre`, /<\/h1>\s*<p class="rap-signature"><span data-l="fr">Un rapport d’<b>Alerte Concours Tunisie<\/b> · concours\.clicvia\.com<\/span>/.test(h));
    const meta = n => (h.match(new RegExp(`<meta (?:name|property)="${n}" content="([^"]*)"`)) || [])[1] || "";
    check(`${c} : aperçu de partage (description et og:description commencent par le nom du site, og:title, og:image, og:url justes)`,
      meta("description").startsWith("Alerte Concours Tunisie — rapport du mois. ") && meta("og:description") === meta("description") && meta("og:title").length > 10
      && !meta("og:title").includes(" | ") && meta("og:url") === url && (c === "rapports/" ? meta("og:image") === "https://concours.clicvia.com/assets/og-image-v2.jpg" && existsSync(join(root, "assets/og-image-v2.jpg")) : meta("og:image").startsWith(url + "apercu-")));
    // image PROPRE à chaque rapport du mois (18/10/2026, Ahmed : sur Facebook, l'aperçu montrait l'image du site, pas l'article)
    if (c !== "rapports/") {
      const og = meta("og:image").replace("https://concours.clicvia.com/", ""), nom = og.split("/").pop();
      const ld = (h.match(/"@type": "Article"[^\n]*"image": "([^"]+)"/) || [])[1];
      check(`${c} : image d'aperçu propre au rapport (apercu-<empreinte>.jpg dans son dossier, < 250 Ko, JPEG 1200 × 630, aussi dans le JSON-LD Article, une seule)`,
        og === c + nom && /^apercu-[0-9a-f]{8}\.jpg$/.test(nom) && existsSync(join(root, og)) && statSync(join(root, og)).size < 250 * 1024
        && (b => b[0] === 0xFF && b[1] === 0xD8 && (() => { for (let i = 2; i < b.length - 8;) { if (b[i] !== 0xFF) return false; const t = b[i + 1], n = b.readUInt16BE(i + 2);
          if (t >= 0xC0 && t <= 0xC3) return b.readUInt16BE(i + 5) === 630 && b.readUInt16BE(i + 7) === 1200; i += 2 + n; } return false; })())(readFileSync(join(root, og)))
        && ld === meta("og:image") && readdirSync(join(root, c)).filter(f => /^apercu-.*\.jpg$/.test(f)).length === 1
        && meta("og:type") === "article");
    }
  }
  const pj = lire("assets/page.js"), css = lire("assets/style.css");
  check("rapports : code du bouton dans page.js (écouteur, navigator.share, copie, message « Lien copié », window.prompt, GoatCounter)", pj.includes('closest("button[data-partage-rapport]")')
    && pj.includes("navigator.share({ title: titre, text: texte, url: url })") && pj.includes("navigator.clipboard.writeText(texte + \" \" + url)") && pj.includes("Lien copié ✓ — collez-le où vous voulez")
    && pj.includes("window.prompt(") && /goatcounter\.count\(\{ path: "partage"/.test(pj) && pj.indexOf("data-partage-rapport") < pj.indexOf(">>> vidéo de présentation"));
  check("rapports : bouton tactile (≥ 44 px de haut) et pas la classe du petit bouton rond .partager", /\.rap-partager\{[^}]*min-height:(4[4-9]|[5-9]\d)px/.test(css) && ![...lire("rapports/index.html").matchAll(/<button class="([^"]*)" type="button" data-partage-rapport/g)].some(m => m[1].split(/\s+/).includes("partager")));
  if (JSDOM) {
    const f = Object.keys(H).length ? `rapports/${Object.keys(H).sort().pop()}/index.html` : "rapports/index.html";
    const essai = async (share, clip) => {
      const dom = new JSDOM(lire(f).replace(/<script[^>]*src="[^"]*"[^>]*><\/script>/g, ""), { runScripts: "outside-only", url: "https://concours.clicvia.com/" + f.replace(/index\.html$/, ""), pretendToBeVisual: true });
      const w = dom.window, journal = { share: null, clip: null, prompt: null, compte: null };
      w.localStorage.setItem("langue", "fr");
      if (share) Object.defineProperty(w.navigator, "share", { value: o => { journal.share = o; return Promise.resolve(); }, configurable: true });
      if (clip) Object.defineProperty(w.navigator, "clipboard", { value: { writeText: t => { journal.clip = t; return Promise.resolve(); } }, configurable: true });
      w.prompt = (a, b) => { journal.prompt = b; return null; };
      w.goatcounter = { count: o => { journal.compte = o; } };
      w.eval(lire("assets/page.js")); w.document.dispatchEvent(new w.Event("DOMContentLoaded"));
      const b = w.document.querySelectorAll("button[data-partage-rapport]")[1];
      b.dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
      await new Promise(r => setTimeout(r, 30));
      return { journal, b, ok: b.parentNode.querySelector(".rap-partage-ok").textContent };
    };
    const t1 = await essai(true, true);
    check("navigateur : rapport → téléphone : menu de partage avec titre, texte « … Rapport du mois d’Alerte Concours Tunisie » et lien ; clic compté", t1.journal.share && t1.journal.share.url === t1.b.dataset.url
      && t1.journal.share.text.includes("Rapport du mois d’Alerte Concours Tunisie") && !t1.journal.clip && t1.journal.compte && t1.journal.compte.path.startsWith("partage/rapports/"));
    const t2 = await essai(false, true);
    check("navigateur : rapport → ordinateur : texte + lien copiés et « Lien copié ✓ » affiché", t2.journal.clip === t2.b.dataset.texte + " " + t2.b.dataset.url && t2.ok.startsWith("Lien copié ✓"));
    const t3 = await essai(false, false);
    check("navigateur : rapport → sans presse-papiers : fenêtre avec le lien", t3.journal.prompt === t3.b.dataset.texte + " " + t3.b.dataset.url);
  }
}
// ---- og:locale lisible par Facebook (18/10/2026) : « fr_TN » / « ar_TN » sont REJETÉS par Facebook (« n'a pas pu être analysée en tant
// que type enum ») et l'aperçu partagé était faux ; valeurs admises : fr_FR, ar_AR, en_US.
{ const pagesLoc = [...sm.matchAll(/<loc>https:\/\/[^/]+\/([^<]*)<\/loc>/g)].map(m => m[1] + "index.html").filter(f => existsSync(join(root, f)));
  const mauvaises = pagesLoc.filter(f => { const h = lire(f); return /_TN"/.test(h) || [...h.matchAll(/property="og:locale(?::alternate)?" content="([^"]+)"/g)].some(m => !["fr_FR", "ar_AR", "en_US"].includes(m[1])); });
  check(`og:locale admis par Facebook (fr_FR / ar_AR / en_US, jamais fr_TN ni ar_TN) sur les ${pagesLoc.length} pages du plan du site`, pagesLoc.length > 3 && mauvaises.length === 0);
  if (mauvaises.length) console.log("   og:locale refusé : " + mauvaises.slice(0, 5).join(", "));
}

// 18/10/2026 (décision d'Ahmed) : motif du paiement = le CODE PERSONNEL, jamais le nom (deux clients peuvent avoir le même nom)
check("paiement : le motif est le code personnel, jamais « nom … (motif du paiement) »",
  !/nom[^<]{0,40}\(motif du paiement\)/.test(lire("alertes/index.html")) && !/motif\s*[:=]\s*(votre )?nom/i.test(lire("alertes/index.html")));
console.log(`\n${ok}/${ok + ko} vérifications réussies` + (ko ? ` — ${ko} ÉCHEC(S) : ne pas publier.` : " — tout est bon."));
process.exit(ko ? 1 : 0);
