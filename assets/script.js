// Minimal, dependency-free behaviour.

// Mobile nav toggle
(function () {
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    // Close menu after tapping a link (mobile)
    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }
})();

// Auto-fill the copyright year
(function () {
  var y = document.getElementById("year");
  if (y) y.textContent = new Date().getFullYear();
})();

// "Last updated" date. ICAI guidelines require the website to show when it was
// last updated. Update the date below whenever you change the site's content.
(function () {
  var el = document.getElementById("last-updated");
  if (!el) return;
  // TODO: change this date whenever you edit the site content.
  el.textContent = "24 June 2026";
})();
