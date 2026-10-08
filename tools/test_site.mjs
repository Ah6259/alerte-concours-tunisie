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

// ---- 1. Données
check("données : au moins 20 concours lus, chacun avec organisme, grade, métier et gouvernorat", D.concours.length >= 20
  && D.concours.every(c => c.organisme && c.grade && c.metier && c.gouvernorat));
check("données : au moins un concours local (gouvernorat) et un national", D.concours.some(c => c.gouvernorat === "national") && D.concours.some(c => GOUVS.includes(c.gouvernorat)));

// ---- 2. Pages : toutes présentes, propres, FR + AR
check("pages : accueil, 24 gouvernorats + national, métiers, guide, alertes, à propos", pages.every(p => existsSync(join(root, p))) && pages.length >= 38);
for (const p of pages) {
  const h = lire(p);
  const ok1 = /<title>[^<]{10,}<\/title>/.test(h) && /name="description" content="[^"]{30,}"/.test(h) && /rel="canonical" href="https:\/\/ah6259\.github\.io\/alerte-concours-tunisie\//.test(h)
    && h.includes('http-equiv="Content-Security-Policy"') && h.includes('content="noai, noimageai"') && h.includes('data-l="ar"') && h.includes("assets/page.js")
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
  pc.every(([c, f]) => existsSync(join(root, f)) && (h => h.includes(`<link rel="canonical" href="https://ah6259.github.io/alerte-concours-tunisie/concours/${c.id}/">`)
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
check("plan du site : les pages des concours", D.concours.every(c => sm.includes(`https://ah6259.github.io/alerte-concours-tunisie/concours/${c.id}/`)));
check("plan du site : toutes les pages", pages.every(p => sm.includes("https://ah6259.github.io/alerte-concours-tunisie/" + p.replace(/index\.html$/, ""))));
const rb = lire("robots.txt");
check("robots.txt : Google autorisé, robots d'IA refusés, plan du site", /User-agent: Googlebot\nAllow: \//.test(rb) && /User-agent: GPTBot\nDisallow: \//.test(rb) && /User-agent: ClaudeBot\nDisallow: \//.test(rb) && rb.includes("sitemap.xml"));
const man = JSON.parse(lire("manifest.webmanifest"));
check("manifeste : id propre au site, icônes présentes", man.id === "/alerte-concours-tunisie/" && man.icons.every(i => existsSync(join(root, i.src))));
check("image d'aperçu WhatsApp et icônes", existsSync(join(root, "assets/og-image-v1.png")) && statSync(join(root, "assets/og-image-v1.png")).size < 300 * 1024
  && existsSync(join(root, "assets/apple-touch-icon.png")) && existsSync(join(root, "favicon.ico")) && existsSync(join(root, "assets/logo.svg")));
check("service worker propre au site", /const PREFIXE = "alerte-concours-tunisie-"/.test(lire("sw.js")) && lire("assets/page.js").includes('register("/alerte-concours-tunisie/sw.js"'));
// jamais le nom d'un site concurrent dans le dépôt public (noms écrits à l'envers ici)
const interdits = ["moc.einisutsruocnoc", "nt.sruocnoceinisut"].map(x => [...x].reverse().join(""));
const tous = []; (function parcourir(d) { for (const f of readdirSync(d)) { const c = join(d, f); if (f === "node_modules" || f === ".git") continue; statSync(c).isDirectory() ? parcourir(c) : /\.(html|js|mjs|py|md|json|txt|xml|css)$/.test(f) && tous.push(c); } })(root);
check("aucun nom de site concurrent dans le dépôt public", tous.every(f => interdits.every(n => !readFileSync(f, "utf8").toLowerCase().includes(n))));

// ---- 4. Comme dans un navigateur : filtres (un concours national reste visible quel que soit le gouvernorat)
let JSDOM = null;
try { ({ JSDOM } = await import("jsdom")); } catch (e) { console.log("(jsdom absent : tests du navigateur ignorés)"); }
if (JSDOM) {
  const html = acc.replace(/<script[^>]*src="[^"]*"[^>]*><\/script>/g, "");
  const dom = new JSDOM(html, { runScripts: "outside-only", url: "https://ah6259.github.io/alerte-concours-tunisie/?jour=" + D.lu_le, pretendToBeVisual: true });
  const w = dom.window; w.localStorage.setItem("langue", "fr");
  for (const js of ["assets/page.js", "assets/app.js"]) w.eval(lire(js));
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
  fg.value = ""; fg.dispatchEvent(new w.Event("change"));
  const fq = d.getElementById("f-q"); fq.value = "zzzzqqq"; fq.dispatchEvent(new w.Event("input"));
  check("navigateur : recherche sans résultat → message « Aucun concours »", ouvertes().length === 0 && !d.getElementById("vide").hidden);
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
check("alertes : prix 15 DT / 3 mois ou 39 DT / an, 7 jours d'essai gratuit, pas de renouvellement automatique",
  /15 DT \/ 3 mois/.test(al) && /39 DT \/ an/.test(al) && /7 jours d'essai gratuit/.test(al) && /Pas de renouvellement automatique/.test(al));
check("alertes : paiement en 3 étapes D17 / IZI au 24 321 390 (logos, écrans d'exemple), phrase de confiance, preuve WhatsApp",
  /<ol class="paie-etapes">/.test(al) && /class="paie-confiance"/.test(al) && al.includes("24 321 390") && /href="https:\/\/wa\.me\/21624321390\?text=/.test(al)
  && ["d17.png", "izi.png", "transfert-d17.svg", "transfert-izi.svg"].every(f => existsSync(join(root, "assets/paiement", f))) && /src="\.\.\/assets\/paiement\/d17\.png"/.test(al));
check("alertes : formulaire Formspree (mwlpakqj) : nom, téléphone, métiers, gouvernorats (+ « Toute la Tunisie »), concours à suivre, formule, conditions",
  /<form id="abo-form" action="https:\/\/formspree\.io\/f\/mwlpakqj"/.test(al) && /name="nom" required/.test(al) && /name="telephone" required/.test(al)
  && (al.match(/name="metiers"/g) || []).length >= 10 && (al.match(/name="gouvernorats"/g) || []).length === 25 && /id="g-tous"/.test(al)
  && /name="suivis"/.test(al) && (al.match(/name="formule"/g) || []).length === 3 && /href="conditions\/"/.test(al));
check("alertes : script externe abonnement.js sur cette page seulement", /<script src="\.\.\/assets\/abonnement\.js\?v=/.test(al) && !/abonnement\.js/.test(acc));
const co = lire("alertes/conditions/index.html");
check("conditions : prix, essai, paiement, arrêt (/stop), données personnelles, non officiel", /15 DT pour 3 mois/.test(co) && /\/stop/.test(co) && /Données personnelles/.test(co) && /pas officiel/.test(co));
check("accueil + pages : gros bouton doré vers alertes/ (7 jours d'essai)", /class="btn-pro-grand" id="btn-alertes" href="alertes\/"/.test(acc) && /7 jours d'essai gratuit/.test(acc)
  && /class="btn-pro-grand" id="btn-alertes" href="\.\.\/\.\.\/alertes\/"/.test(lire(`gouvernorat/${GOUVS[0]}/index.html`)));
check("sitemap : alertes/ et alertes/conditions/", sm.includes("alertes/</loc>") && sm.includes("alertes/conditions/</loc>"));
check("aucune donnée d'abonné dans ce dépôt public (abonnes.json, chat_id, jeton Telegram)",
  !existsSync(join(root, "abonnes.json")) && !existsSync(join(root, "donnees/abonnes.json")) && !/chat_id|bot\d{6,}:/.test(al + lire("assets/abonnement.js")));
if (JSDOM) {
  const envois = [];
  const dom = new JSDOM(al, { runScripts: "outside-only", url: "https://ah6259.github.io/alerte-concours-tunisie/alertes/", pretendToBeVisual: true });
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
}

console.log(`\n${ok}/${ok + ko} vérifications réussies` + (ko ? ` — ${ko} ÉCHEC(S) : ne pas publier.` : " — tout est bon."));
process.exit(ko ? 1 : 0);
