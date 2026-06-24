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

// Enquiry form — submit to Formspree via AJAX so the visitor stays on the page
// and sees an inline confirmation instead of being redirected.
(function () {
  var form = document.getElementById("enquiry-form");
  var status = document.getElementById("form-status");
  if (!form || !status) return;

  function setStatus(msg, type) {
    status.textContent = msg;
    status.className = "form-status " + (type || "");
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();

    // Guard: the Formspree form ID hasn't been set up yet.
    if (form.action.indexOf("YOUR_FORM_ID") !== -1) {
      setStatus(
        "The enquiry form isn't connected yet. Please email us directly using the address above.",
        "error"
      );
      return;
    }

    var btn = form.querySelector("button[type=submit]");
    var original = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Sending…";
    setStatus("", "");

    fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: { Accept: "application/json" },
    })
      .then(function (res) {
        if (res.ok) {
          form.reset();
          setStatus("Thank you — your enquiry has been sent. We'll be in touch.", "success");
        } else {
          return res.json().then(function (data) {
            var msg =
              data && data.errors
                ? data.errors.map(function (er) { return er.message; }).join(", ")
                : "Something went wrong. Please email us directly instead.";
            setStatus(msg, "error");
          });
        }
      })
      .catch(function () {
        setStatus("Network error — please email us directly instead.", "error");
      })
      .finally(function () {
        btn.disabled = false;
        btn.textContent = original;
      });
  });
})();
