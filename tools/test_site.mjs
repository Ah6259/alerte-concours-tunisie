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
const pages = ["index.html", "actualites/index.html", "guide-inscription/index.html", "alertes/index.html", "a-propos/index.html",
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
    && h.includes('class="officiel" href="https://www.concours.gov.tn/') && h.includes('href="../../guide-inscription/"')
    && h.includes(c.grade.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;")) && !/undefined|NaN|None/.test(h))(lire(f))));
check("cartes : le grade mène à la page du concours", D.concours.filter(c => acc.includes(`id="c-${c.id}"`)).every(c => acc.includes(`href="concours/${c.id}/"`)) && acc.includes('href="concours/'));
// carte de la Tunisie (08/10/2026, comme les autres sites) : 24 bulles cliquables sur l'accueil ; sur une page de gouvernorat, la sienne en surbrillance
const bullesAcc = [...acc.matchAll(/<a href="gouvernorat\/([a-z-]+)\/" class="tn-b[^"]*" data-gouv="([a-z-]+)"/g)];
check("carte de la Tunisie : 24 gouvernorats sur l'accueil, chaque bulle mène à sa page", bullesAcc.length === 24 && bullesAcc.every(m => m[1] === m[2] && GOUVS.includes(m[1])));
check("carte de la Tunisie : nombres recalculés par le navigateur seulement sur l'accueil (sinon 0 partout sur une page de gouvernorat)", /if \(document\.getElementById\("f-gouv"\)\) document\.querySelectorAll\("\.tn-b\[data-gouv\] text"\)/.test(lire("assets/app.js")));
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

console.log(`\n${ok}/${ok + ko} vérifications réussies` + (ko ? ` — ${ko} ÉCHEC(S) : ne pas publier.` : " — tout est bon."));
process.exit(ko ? 1 : 0);
