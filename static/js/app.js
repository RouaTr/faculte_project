(function () {
  // Menu latéral (mobile)
  var sidebar = document.getElementById("sidebar");
  var scrim = document.getElementById("scrim");
  var burger = document.getElementById("menu-toggle");
  function setMenu(open) {
    if (!sidebar) return;
    sidebar.classList.toggle("is-open", open);
    if (scrim) scrim.hidden = !open;
    if (burger) burger.setAttribute("aria-expanded", String(open));
  }
  if (burger) burger.addEventListener("click", function () { setMenu(!sidebar.classList.contains("is-open")); });
  if (scrim) scrim.addEventListener("click", function () { setMenu(false); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") setMenu(false); });

  // Messages : fermeture manuelle et automatique
  document.querySelectorAll(".toast").forEach(function (toast) {
    var close = toast.querySelector("button");
    if (close) close.addEventListener("click", function () { toast.remove(); });
    if (!toast.classList.contains("toast-error")) setTimeout(function () { toast.remove(); }, 6000);
  });

  // Confirmation avant une action importante
  document.addEventListener("click", function (e) {
    var el = e.target.closest("[data-confirm]");
    if (el && !window.confirm(el.getAttribute("data-confirm"))) e.preventDefault();
  });

  // Évite les doubles envois
  document.querySelectorAll("form").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (e.defaultPrevented) return;
      var btn = e.submitter;
      if (btn && !btn.name) setTimeout(function () { btn.disabled = true; }, 0);
    });
  });

  // Formulaire utilisateur : affiche le profil correspondant au rôle
  var role = document.querySelector("[data-role-select]");
  if (role) {
    var sections = document.querySelectorAll("[data-profile]");
    var sync = function () {
      sections.forEach(function (s) { s.hidden = s.getAttribute("data-profile") !== role.value; });
    };
    role.addEventListener("change", sync);
    sync();
  }
})();
