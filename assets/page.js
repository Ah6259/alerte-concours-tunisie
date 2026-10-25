/* Langue (français / arabe), en-tête et pied de page communs, petites fonctions */
// La mémoire du navigateur est PARTAGÉE par tous les sites d'ah6259.github.io : n'accepter que « fr » ou « ar »
// (le site des conférences gardait « en » → textes tous cachés)
(function () {
  const html = document.documentElement;
  const racine = html.dataset.racine || "";
  let langue = "fr";
  try { langue = (/^(fr|ar)$/.test(localStorage.getItem("langue") || "") ? localStorage.getItem("langue") : "") || (navigator.language || "").startsWith("ar") && "ar" || "fr"; } catch (e) {}
  const demande = new URLSearchParams(location.search).get("lang");
  if (demande === "ar" || demande === "fr") langue = demande;

  window.T = (fr, ar) => html.lang === "ar" ? ar : fr;
  // Nombres et dates isolés dans un texte arabe (U+2066 … U+2069)
  window.iso = t => "⁦" + t + "⁩";

  function cadre() {
    const e = document.getElementById("entete");
    if (e) e.innerHTML = `
      <div class="wrap">
        <a class="logo" href="${racine || "./"}">
          <img class="logo-mark" src="${racine}assets/logo.svg" alt="" width="34" height="34">
          <span class="logo-nom">${T("Alerte Concours", "تنبيه المناظرات")}
            <small>${T("Tunisie · tous les concours publics, 24 gouvernorats", "تونس · كل المناظرات العمومية في 24 ولاية")}</small></span>
        </a>
        <div class="entete-boutons">
          <a class="entete-pro" href="${racine}alertes/">${T("Alertes", "التنبيهات")}</a>
          <button class="partager" type="button" aria-label="${T("Partager cette page", "شارك هذه الصفحة")}" title="${T("Partager", "شارك")}"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/></svg></button>
          <button class="langue" type="button" aria-label="${T("Lire en arabe", "Lire en français")}" title="${T("العربية", "Français")}">${T("ع", "Fr")}</button>
        </div>
      </div>`;
    const p = document.getElementById("pied");
    const maj = document.body.dataset.majTexte || "";
    if (p) p.innerHTML = `
      <div class="wrap">
        <div class="pied-logo"><img src="${racine}assets/logo.svg" alt="" width="24" height="24"> ${T("Alerte Concours Tunisie", "تنبيه المناظرات تونس")}</div>
        <nav>
          <a href="${racine || "./"}">${T("Tous les concours ouverts", "كل المناظرات المفتوحة")}</a>
          <a href="${racine}#gouvernorats">${T("Par gouvernorat", "حسب الولاية")}</a>
          <a href="${racine}#metiers">${T("Par métier", "حسب الاختصاص")}</a>
          <a href="${racine}guide-inscription/">${T("S'inscrire à un concours", "كيف تترشح لمناظرة")}</a>
          <a href="${racine}rapports/">${T("Rapports du mois", "التقارير الشهرية")}</a>
          <a href="${racine}alertes/">${T("Alertes par métier et gouvernorat", "تنبيهات حسب الاختصاص والولاية")}</a>
          <a href="${racine}a-propos/">${T("Comment fonctionne le site ?", "كيف يعمل الموقع؟")}</a>
          <a href="${racine}#avis">${T("Votre avis", "رأيك")}</a>
        <a href="https://clicvia.com/" rel="noopener" target="_blank">${T("Tous nos services", "كل خدماتنا")}</a>
        </nav>
        <p>${T(`Source : <a href="https://www.concours.gov.tn/" rel="noopener">portail officiel des concours publics</a> (concours.gov.tn). Chaque concours renvoie au portail officiel, où se fait l'inscription.`,
               `المصدر: <a href="https://www.concours.gov.tn/" rel="noopener">البوابة الرسمية للمناظرات العمومية</a> (${iso("concours.gov.tn")}). كل مناظرة مرفقة برابط البوابة الرسمية حيث يتم الترشح.`)}</p>
        ${maj ? `<p>${T("Dernière lecture de la source : ", "آخر قراءة للمصدر: ")}${iso(maj)}</p>` : ""}
        <p>${T("Site indépendant, non officiel : informations indicatives, seul le portail officiel fait foi. Les noms des organismes appartiennent à leurs propriétaires.",
               "موقع مستقل وغير رسمي: معلومات للإرشاد فقط، والبوابة الرسمية هي المرجع الوحيد. أسماء الهياكل ملك لأصحابها.")}</p>
        <p>© 2026 ${T("Alerte Concours Tunisie — tous droits réservés.", "تنبيه المناظرات تونس — جميع الحقوق محفوظة.")}</p>
      </div>`;
    document.querySelectorAll(".langue").forEach(b =>
      b.addEventListener("click", () => appliquer(html.lang === "ar" ? "fr" : "ar")));
    // bouton Partager (demande d'Ahmed) : menu de partage du téléphone, sinon WhatsApp avec le lien de la page
    document.querySelectorAll(".partager").forEach(b => b.addEventListener("click", async () => {
      const url = location.href.split("#")[0].replace(/[?&]lang=(fr|ar)/, ""), titre = document.title.split(" | ")[0];
      try { if (window.goatcounter && window.goatcounter.count) window.goatcounter.count({ path: "partage" + location.pathname.replace(/^\/alerte-concours-tunisie\//, "/"), title: "Partage", event: true }); } catch (e) {}
      return window.partagerLien();
    }));
  }

  function appliquer(l) {
    html.lang = l; html.dir = l === "ar" ? "rtl" : "ltr";
    try { localStorage.setItem("langue", l); } catch (e) {}
    cadre();
    document.dispatchEvent(new Event("langue"));
  }
  document.addEventListener("DOMContentLoaded", () => appliquer(langue));

  // ---- Protection légère contre la copie (sans gêner les visiteurs) -------------------------
  // 1) Pas d'affichage dans le cadre (iframe) d'un autre site.
  try {
    if (window.top !== window.self && window.top.location.hostname !== location.hostname) window.top.location = location.href;
  } catch (e) { try { window.top.location = location.href; } catch (e2) {} }
  // 2) Images et photos : ni clic droit ni glisser-déposer.
  const estImage = t => t && t.closest && t.closest("img, svg, .hero-photo, .carte-tn");
  document.addEventListener("contextmenu", e => { if (estImage(e.target) && !e.target.closest("a, input, textarea")) e.preventDefault(); });
  document.addEventListener("dragstart", e => { if (estImage(e.target)) e.preventDefault(); });
  // 3) Texte copié depuis une carte : on ajoute la source et la mention « tous droits réservés ».
  document.addEventListener("copy", e => {
    const sel = window.getSelection ? String(window.getSelection()) : "";
    const n = window.getSelection && window.getSelection().anchorNode;
    const el = n && (n.nodeType === 1 ? n : n.parentElement);
    if (!sel || !el || !el.closest || !el.closest(".ao, .liste, main") || el.closest("input, textarea")) return;
    if (!e.clipboardData) return;
    e.clipboardData.setData("text/plain", sel + "\n\nSource : " + location.href.split("#")[0] + " — © Alerte Concours Tunisie, tous droits réservés.");
    e.preventDefault();
  });
})();

/* Installation sur le téléphone : service worker PRUDENT (sw.js : réseau d'abord pour les pages et les données).
   Seulement en https (jamais en file: pendant les tests locaux). */
if ("serviceWorker" in navigator && location.protocol === "https:") {
  window.addEventListener("load", () => {
    try { navigator.serviceWorker.register(BASE_SITE + "sw.js", { scope: BASE_SITE }).catch(() => {}); } catch (e) { /* rien : le site marche sans */ }
  });
}

/* Rapports du mois (18/10/2026, demande d'Ahmed) : UN SEUL bouton « Partager ce rapport » (button[data-partage-rapport],
   fabriqué par robot/rapports.py). Téléphone : menu de partage (Facebook, WhatsApp, LinkedIn…) ; ordinateur : texte + lien
   copiés, sinon fenêtre avec le lien. Le texte dit de quel site vient l'article. */
document.addEventListener("click", function (e) {
  var b = e.target && e.target.closest && e.target.closest("button[data-partage-rapport]");
  if (!b) return;
  e.preventDefault();
  var ar = document.documentElement.lang === "ar";
  var url = b.getAttribute("data-url"), titre = b.getAttribute("data-titre") || document.title.split(" | ")[0];
  var texte = (ar && b.getAttribute("data-texte-ar")) || b.getAttribute("data-texte") || titre;
  var zone = b.parentNode && b.parentNode.querySelector(".rap-partage-ok");
  try { if (window.goatcounter && window.goatcounter.count) window.goatcounter.count({ path: "partage" + location.pathname.replace(/^\/alerte-concours-tunisie\//, "/"), title: "Partage", event: true }); } catch (x) {}
  function message() {
    if (!zone) return;
    zone.textContent = ar ? "تم نسخ الرابط ✓ — ألصقه حيث تريد" : "Lien copié ✓ — collez-le où vous voulez";
    clearTimeout(zone._t); zone._t = setTimeout(function () { zone.textContent = ""; }, 4000);
  }
  function fenetre() { try { window.prompt(ar ? "انسخ هذا الرابط:" : "Copiez ce lien :", texte + " " + url); } catch (x) {} }
  function copier() {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) return navigator.clipboard.writeText(texte + " " + url).then(message, fenetre);
    } catch (x) {}
    fenetre();
  }
  if (navigator.share) {
    try {
      navigator.share({ title: titre, text: texte, url: url }).catch(function (x) { if (!x || x.name !== "AbortError") copier(); });
      return;
    } catch (x) {}
  }
  copier();
});

/* >>> vidéo de présentation : page video/ partagée par le bouton « Partager » (outil vidéos d'Ahmed) */
/* Adresse du site (11 octobre 2026) : concours.clicvia.com (racine « / ») ; l'ancienne adresse ah6259.github.io/alerte-concours-tunisie/ redirige
   vers elle. BASE_SITE = dossier du site selon l'adresse ; GoatCounter garde le préfixe /alerte-concours-tunisie (compteur commun). */
var BASE_SITE = /\.github\.io$/.test(location.hostname) ? "/alerte-concours-tunisie/" : "/";
window.goatcounter = window.goatcounter || {};
window.goatcounter.path = function (p) { return BASE_SITE === "/" ? "/alerte-concours-tunisie" + p : p; };
window.VIDEO_SITE = {"base": BASE_SITE, "defaut": "fr", "video": false, "nom": {"fr": "Alerte Concours Tunisie", "ar": "تنبيه المناظرات تونس"}};
/* « video": false » (25/10/2026) : la page video/ n'existe pas encore -> aucun lien « Vidéo de présentation » et le bouton
   « Partager » partage la page en cours. Le jour où la vidéo est faite : retirer « "video": false » (pas de vidéo = pas de lien). */
/* Bouton « Partager » (demande d'Ahmed, octobre 2026) : partage un LIEN vers la page vidéo du site (qui montre la vidéo
   de présentation, avec un gros bouton « Ouvrir le site ») + l'adresse du site dans le texte. WhatsApp et Facebook
   affichent l'aperçu de la page vidéo (grande image, vidéo lisible sur Facebook). Menu de partage du téléphone, sinon WhatsApp.
   Espace professionnels des annuaires : page « video-pro/ ». Réglages : window.VIDEO_SITE (juste au-dessus). */
(function () {
  var S = window.VIDEO_SITE, ORIGINE = S.base === "/" ? "https://concours.clicvia.com" : "https://ah6259.github.io";
  function langue() { return document.documentElement.lang || S.defaut; }
  function M(o) { return o[langue()] || o[S.defaut] || o.fr; }
  // page vidéo à partager (et page du site correspondante) selon la page où l'on est
  window.pageVideo = function () {
    var chemin = location.pathname, pro = false;
    for (var i = 0; i < (S.pro || []).length; i++) if (chemin.indexOf(S.base + S.pro[i]) === 0) pro = true;
    var l = langue(), q = l !== S.defaut ? "?lang=" + l : "";
    return { page: ORIGINE + S.base + (pro ? "video-pro/" : "video/") + q, site: ORIGINE + S.base + (pro ? S.site_pro : "") + q + (pro ? (S.ancre_pro || "") : ""),
             titre: M(pro ? S.titre_pro : S.nom) };
  };
  window.partagerLien = function (titre, site) {
    var v = window.pageVideo(), t = titre || v.titre, texte;
    if (site) v.site = site;
    if (S.video === false) {
      t = titre || document.title.split(" | ")[0] || v.titre;
      v.page = site || (location.origin + location.pathname).replace(/index\.html$/, "");
      texte = t;
    } else {
      texte = t + "\n" + M({ fr: "Le site : ", ar: "الموقع: ", en: "The website: " }) + v.site + "\n" + M({ fr: "Regardez la vidéo :", ar: "شاهد الفيديو:", en: "Watch the video:" });
    }
    function whatsapp() { window.open("https://wa.me/?text=" + encodeURIComponent(texte + " " + v.page), "_blank", "noopener"); return "whatsapp"; }
    if (navigator.share) {
      return navigator.share({ title: t, text: texte, url: v.page }).then(function () { return "lien"; }, function (e) {
        return e && e.name === "AbortError" ? "annule" : whatsapp();
      });
    }
    return Promise.resolve(whatsapp());
  };
  // page vidéo : textes dans la langue de la page (data-vfr / data-var / data-ven), vidéo de la langue (data-src-fr…)
  function traduire() {
    var l = langue();
    var el = document.querySelectorAll("[data-vfr]");
    for (var i = 0; i < el.length; i++) { var t = el[i].getAttribute("data-v" + l) || el[i].getAttribute("data-v" + S.defaut); if (t && el[i].textContent !== t) el[i].textContent = t; }
    var v = document.querySelector(".video-lecteur");
    if (v) {
      var s = v.getAttribute("data-src-" + l) || v.getAttribute("data-src-defaut") || v.getAttribute("src");
      if (!v.getAttribute("data-src-defaut")) v.setAttribute("data-src-defaut", v.getAttribute("src"));
      if (v.getAttribute("src") !== s) v.setAttribute("src", s);
      if (!v.getAttribute("data-poster-defaut")) v.setAttribute("data-poster-defaut", v.getAttribute("poster"));
      var po = v.getAttribute("data-poster-" + l) || v.getAttribute("data-poster-defaut");
      if (v.getAttribute("poster") !== po) v.setAttribute("poster", po);
    }
    // lien discret « Vidéo de présentation » en bas de l'accueil et de À propos -> la page vidéo
    var p = location.pathname.replace(/index\.html$/, "");
    if (S.video === false) { var ancien = document.getElementById("lien-video"); if (ancien) ancien.remove(); }
    else if (p === S.base || p === S.base + "a-propos/") {
      var b = document.getElementById("lien-video");
      if (!b) {
        b = document.createElement("p"); b.id = "lien-video"; b.className = "lien-video"; b.appendChild(document.createElement("a"));
        var m = document.querySelector("main"); if (m) m.insertAdjacentElement("afterend", b); else document.body.appendChild(b);
      }
      b.firstChild.href = S.base + "video/" + (l !== S.defaut ? "?lang=" + l : "");
      b.firstChild.textContent = M({ fr: "Vidéo de présentation", ar: "الفيديو التقديمي", en: "Presentation video" });
    }
  }
  document.addEventListener("click", function (e) {
    var b = e.target && e.target.closest && e.target.closest("[data-partager-video]");
    if (!b) return;
    e.preventDefault();
    try { if (window.goatcounter && window.goatcounter.count) window.goatcounter.count({ path: "partage" + location.pathname.replace(S.base, "/"), title: "Partage", event: true }); } catch (x) {}
    window.partagerLien();
  });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { setTimeout(traduire, 0); }); else setTimeout(traduire, 0);
  document.addEventListener("langue", function () { setTimeout(traduire, 0); });
  try { new MutationObserver(function () { setTimeout(traduire, 0); }).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] }); } catch (x) {}
})();
/* <<< vidéo de présentation */
