/* Inscription « Alertes concours » (page alertes/) — repris d'Alertes appels d'offres le 08/10/2026.
   - Rien n'est envoyé sans clic sur « Envoyer mon inscription ».
   - Envoi à Formspree (formulaire mwlpakqj, le même que « Votre avis ») sans quitter la page.
   - Les métiers et gouvernorats cochés sont envoyés en UNE ligne chacun (ex. « btp-genie-civil, informatique »),
     prête à recopier dans le bouton GitHub « activer-abonne » du dépôt privé « concours-abonnes ».
   - E-mail et téléphone OBLIGATOIRES (règle d'Ahmed du 24/11/2026 : e-mail automatique avec le code et le paiement).
   - Concours à suivre (facultatif) : numéros nettoyés (chiffres seulement, 10 au plus).
   - Après l'envoi : le formulaire est remplacé par la page « Dernière étape » (parcours commun des Pass, règle commune § 70,
     25/11/2026) : code de commande en gros (= motif du paiement), paiement en 3 étapes, WhatsApp pré-rempli avec le code,
     filet « oublié le code ? », puis Telegram.
   - Le téléphone se souvient de la commande (localStorage « pass-commande » : code, formule, date, lien Telegram ; JAMAIS nom,
     téléphone ni e-mail ; gardée 60 jours) : en revenant, bandeau « Votre commande en attente » + paiement + WhatsApp +
     « Ouvrir Telegram » + « Nouvelle commande ». Pas de vérification d'activation sur ce site (alertes sur Telegram).
   - Fichier externe : aucun script en ligne (CSP). Textes en français et en arabe selon la langue de la page. */
(function () {
  var ADRESSE = "https://formspree.io/f/mwlpakqj";
  var ar = function () { return document.documentElement.lang === "ar"; };
  var T = function (fr, a) { return ar() ? a : fr; };
  var SITE_FR = "Alerte Concours Tunisie", SITE_AR = "تنبيه المناظرات تونس", WA = "21624321390";
  var FORMULES_AR = { "3 mois": "3 أشهر", "1 an": "سنة" };
  var CLE = "pass-commande", JOURS = 60, FORMAT = /^[A-HJ-NP-Z2-9]{6}$/;
  var formuleLue = function (f) { return T(f, FORMULES_AR[f] || f); };
  // message WhatsApp de la preuve de paiement : le client n'a rien à recopier (code + formule déjà dedans)
  function lienWa(code, formule) {
    return "https://wa.me/" + WA + "?text=" + encodeURIComponent(T(
      "Voici ma preuve de paiement — " + SITE_FR + " — code " + code + " — " + formuleLue(formule),
      "هذا وصل الدفع — " + SITE_AR + " — الرمز " + code + " — " + formuleLue(formule)));
  }
  // remplit toute la page : code (gros + motif), formule, liens WhatsApp, liens Telegram
  function remplir(code, formule, tg) {
    var i, x = document.querySelectorAll("[data-code]");
    for (i = 0; i < x.length; i++) x[i].textContent = code;
    x = document.querySelectorAll("[data-formule]");
    for (i = 0; i < x.length; i++) x[i].textContent = formuleLue(formule);
    x = document.querySelectorAll("a.btn-wa");
    for (i = 0; i < x.length; i++) x[i].setAttribute("href", lienWa(code, formule));
    x = document.querySelectorAll("a[data-tg]");
    for (i = 0; i < x.length; i++) if (tg) x[i].setAttribute("href", tg);
  }
  function aujourdhui() { return new Date().toISOString().slice(0, 10); }
  function memoriser(code, formule, tg) {
    try { localStorage.setItem(CLE, JSON.stringify({ code: code, formule: formule, date: aujourdhui(), tg: tg })); } catch (e) {}
  }
  function oublier() { try { localStorage.removeItem(CLE); } catch (e) {} }
  // commande gardée : seulement si le code est au bon format, le lien Telegram est le nôtre et elle a moins de 60 jours
  function relire() {
    var c = null;
    try { c = JSON.parse(localStorage.getItem(CLE) || "null"); } catch (e) { c = null; }
    if (!c) return null;
    var t = Date.parse(String(c.date || "") + "T00:00:00Z");
    if (!FORMAT.test(c.code || "") || !(t > 0) || Date.now() - t > JOURS * 864e5 || (c.tg && !/^https:\/\/t\.me\//.test(c.tg))) { oublier(); return null; }
    return c;
  }
  window.PASS_COMMANDE = { cle: CLE, jours: JOURS, relire: relire };

  function coches(form, nom) {
    var res = [], c = form.querySelectorAll('input[name="' + nom + '"]');
    for (var i = 0; i < c.length; i++) if (c[i].checked) res.push(c[i].value);
    return res;
  }
  // téléphone tunisien : 8 chiffres (on accepte les espaces et l'indicatif 216)
  function telephone(v) {
    var n = String(v || "").replace(/\D/g, "");
    if (n.length === 11 && n.indexOf("216") === 0) n = n.slice(3);
    return n.length === 8 ? n : "";
  }

  // même calcul que decoder_choix() du robot privé (concours-abonnes) : listes TRIÉES, 5 cases par caractère, « x » = tous
  var B32 = "0123456789abcdefghijklmnopqrstuv", ALPH = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  function encoder(choix, liste) {
    if (choix.indexOf("tous") >= 0) return "x";
    var s = "";
    for (var k = 0; k < Math.ceil(liste.length / 5); k++) {
      var v = 0;
      for (var j = 0; j < 5; j++) if (5 * k + j < liste.length && choix.indexOf(liste[5 * k + j]) >= 0) v |= 1 << j;
      s += B32[v];
    }
    return s;
  }
  function nouveauCode() {
    var t = new Uint8Array(6), c = "";
    try { crypto.getRandomValues(t); } catch (e) { for (var k = 0; k < 6; k++) t[k] = Math.floor(Math.random() * 256); }
    for (var i = 0; i < 6; i++) c += ALPH[t[i] % ALPH.length];
    return c;
  }
  window.ESSAI_ALERTES = { encoder: encoder };

  function brancher() {
    var form = document.getElementById("abo-form");
    if (!form || form.getAttribute("data-branche")) return;
    form.setAttribute("data-branche", "1");
    var statut = document.getElementById("abo-status");
    var bouton = form.querySelector("button[type=submit]");
    var apres = document.getElementById("apres-abo");
    var dire = function (classe, fr, a) { statut.className = classe; statut.textContent = T(fr, a); };

    // retour sur la page : la commande en attente est montrée à la place du formulaire
    var attente = document.getElementById("abo-attente"), cmd = relire();
    if (cmd && attente) { remplir(cmd.code, cmd.formule, cmd.tg); attente.hidden = false; form.hidden = true; }
    var nouvelle = document.getElementById("abo-nouvelle");
    if (nouvelle) nouvelle.addEventListener("click", function () {
      oublier();
      if (attente) attente.hidden = true;
      if (apres) apres.hidden = true;
      form.hidden = false;
      var n = champ0("nom"); if (n && n.focus) n.focus();
    });
    function champ0(n) { return form.querySelector('[name="' + n + '"]'); }

    // « Toute la Tunisie » et les gouvernorats un par un s'excluent
    var tous = document.getElementById("g-tous");
    form.addEventListener("change", function (e) {
      var c = e.target;
      if (!c || c.name !== "gouvernorats") return;
      var g = form.querySelectorAll('input[name="gouvernorats"]');
      for (var i = 0; i < g.length; i++) {
        if (c === tous && c.checked && g[i] !== tous) g[i].checked = false;
        if (c !== tous && c.checked && tous) tous.checked = false;
      }
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (bouton.disabled) return;
      var val = function (n) { var x = form.querySelector('[name="' + n + '"]'); return x ? String(x.value || "").trim() : ""; };
      var champ = function (n) { return form.querySelector('[name="' + n + '"]'); };
      var tel = telephone(val("telephone"));
      var metiers = coches(form, "metiers"), gouv = coches(form, "gouvernorats");
      var suivis = (val("suivis").match(/\d{1,6}/g) || []).slice(0, 10);
      if (!val("nom")) { dire("err", "Indiquez votre nom.", "اكتب اسمك."); champ("nom").focus(); return; }
      if (!tel) { dire("err", "Téléphone : 8 chiffres, par exemple 24 321 390.", "الهاتف: ⁦8⁩ أرقام، مثال ⁦24 321 390⁩."); champ("telephone").focus(); return; }
      if (!val("email")) { dire("err", "Indiquez votre e-mail : vous y recevez votre code et les étapes du paiement.", "اكتب بريدك الإلكتروني: يصلك عليه رمزك وخطوات الدفع."); champ("email").focus(); return; }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(val("email"))) { dire("err", "Indiquez une adresse e-mail valide.", "اكتب بريدًا إلكترونيًا صحيحًا."); champ("email").focus(); return; }
      if (!metiers.length) { dire("err", "Cochez au moins un métier.", "اختر اختصاصًا واحدًا على الأقل."); return; }
      if (!gouv.length) { dire("err", "Cochez au moins un gouvernorat (ou « Toute la Tunisie »).", "اختر ولاية واحدة على الأقل (أو «كل الولايات»)."); return; }
      if (!champ("conditions").checked) { dire("err", "Cochez « J'accepte les conditions de l'abonnement ».", "يجب الموافقة على شروط الاشتراك."); return; }

      // Code personnel créé ici + lien Telegram qui contient les choix (le robot crée l'inscription, en attente du paiement :
      // aucun essai depuis le 20/10/2026)
      var code = nouveauCode();
      var lien = "https://t.me/" + form.getAttribute("data-robot") + "?start=e" + code + "_" +
        encoder(metiers, (form.getAttribute("data-metiers") || "").split(",")) + "_" + encoder(gouv, (form.getAttribute("data-gouv") || "").split(","));
      var coche = form.querySelector('input[name="formule"]:checked'), formule = coche ? coche.value : "3 mois";
      var fini = function () {
        remplir(code, formule, lien);                          // code en gros, motif, WhatsApp pré-rempli, « Ouvrir Telegram »
        memoriser(code, formule, lien);                        // le téléphone se souvient de la commande (rien de personnel)
        form.hidden = true;
        if (apres) { apres.hidden = false; if (apres.scrollIntoView) try { apres.scrollIntoView({ block: "start" }); } catch (x) {} }
      };
      var piege = champ("_gotcha");
      if (piege && piege.value) { fini(); return; }          // rempli = robot : rien n'est envoyé

      champ("page").value = location.href.split("#")[0];
      var donnees = new FormData(form);
      donnees.delete("metiers"); donnees.delete("gouvernorats");
      donnees.set("telephone", tel);
      donnees.set("metiers", metiers.join(", "));
      donnees.set("gouvernorats", gouv.join(", "));
      donnees.set("suivis", suivis.join(", "));
      donnees.set("code", code);                               // code personnel (motif du paiement)
      // ligne prête pour le bouton « activer-abonne » (dépôt privé)
      donnees.set("pour_activer", "nom: " + val("nom") + " ; telephone: " + tel +
        " ; metiers: " + metiers.join(",") + " ; gouvernorats: " + gouv.join(",") + " ; suivis: " + suivis.join(",") + " ; code: " + code);
      bouton.disabled = true;
      dire("", "Envoi…", "جارٍ الإرسال…");
      fetch(ADRESSE, { method: "POST", body: donnees, headers: { "Accept": "application/json" } })
        .then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          dire("ok", "Merci ! Votre inscription a bien été envoyée.", "شكرًا! تم إرسال تسجيلك.");
          fini();
        })
        .catch(function () {
          // l'inscription ne dépend pas de cet envoi : le robot Telegram la crée seul ; on continue quand même
          dire("", "Inscription non envoyée (connexion), mais votre code fonctionne : ouvrez Telegram ci-dessous.",
               "لم يُرسل التسجيل (الاتصال)، لكن رمزك يعمل: افتح تيليغرام أسفله.");
          fini();
        })
        .then(function () { bouton.disabled = false; });
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", brancher);
  else brancher();
})();
