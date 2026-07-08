(function () {
  "use strict";

  var prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ----------------------------------------
     Mobile nav toggle
  ---------------------------------------- */
  var navToggle = document.getElementById("navToggle");
  var mainNav = document.getElementById("mainNav");

  if (navToggle && mainNav) {
    navToggle.addEventListener("click", function () {
      var isOpen = mainNav.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    mainNav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        mainNav.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  /* ----------------------------------------
     Terminal deploy animation
  ---------------------------------------- */
  var terminalBody = document.getElementById("terminalBody");

  var script = [
    { text: "$ forge deploy --plan dedicated --region syd", cls: "line-prompt", pause: 500 },
    { text: "> resolving nearest available node...", cls: "line-muted", pause: 550 },
    { text: "> node selected: syd-02 (0.4ms internal)", cls: "line-muted", pause: 500 },
    { text: "> provisioning NVMe volume (80GB)...", cls: "line-muted", pause: 600 },
    { text: "> applying network + firewall rules...", cls: "line-muted", pause: 550 },
    { text: "> booting kernel...", cls: "line-muted", pause: 650 },
    { text: "> server ready ✔  4.2s", cls: "line-ok", pause: 1200 },
    { text: "$ forge status", cls: "line-prompt", pause: 500 },
    { text: "> uptime 99.99%  ·  load 0.08  ·  region syd-02", cls: "line-ok", pause: 2600 }
  ];

  function typeLine(container, text, cls, charDelay) {
    return new Promise(function (resolve) {
      var lineEl = document.createElement("div");
      if (cls) lineEl.className = cls;
      container.appendChild(lineEl);

      var cursor = document.createElement("span");
      cursor.className = "terminal-cursor";
      lineEl.appendChild(cursor);

      var i = 0;
      function step() {
        if (i <= text.length) {
          lineEl.textContent = text.slice(0, i);
          lineEl.appendChild(cursor);
          i++;
          setTimeout(step, charDelay);
        } else {
          cursor.remove();
          resolve();
        }
      }
      step();
    });
  }

  function runTerminalScript() {
    if (!terminalBody) return;
    terminalBody.innerHTML = "";

    if (prefersReducedMotion) {
      script.forEach(function (line) {
        var el = document.createElement("div");
        el.className = line.cls;
        el.textContent = line.text;
        terminalBody.appendChild(el);
      });
      return;
    }

    var chain = Promise.resolve();
    script.forEach(function (line) {
      chain = chain.then(function () {
        return typeLine(terminalBody, line.text, line.cls, 16).then(function () {
          return new Promise(function (r) { setTimeout(r, line.pause); });
        });
      });
    });
    chain.then(function () {
      setTimeout(runTerminalScript, 1500);
    });
  }

  runTerminalScript();

  /* ----------------------------------------
     Network node grid
  ---------------------------------------- */
  var nodes = [
    { city: "Sydney", region: "Australia", ping: 8 },
    { city: "Singapore", region: "Southeast Asia", ping: 11 },
    { city: "Tokyo", region: "Japan", ping: 9 },
    { city: "Frankfurt", region: "Germany", ping: 7 },
    { city: "London", region: "United Kingdom", ping: 6 },
    { city: "New York", region: "United States", ping: 5 },
    { city: "Los Angeles", region: "United States", ping: 9 },
    { city: "São Paulo", region: "Brazil", ping: 12 }
  ];

  var networkGrid = document.getElementById("networkGrid");
  if (networkGrid) {
    nodes.forEach(function (node) {
      var card = document.createElement("div");
      card.className = "node-card";
      card.innerHTML =
        '<span class="node-info">' +
          '<span class="node-dot" aria-hidden="true"></span>' +
          '<span>' +
            '<span class="node-city">' + node.city + '</span>' +
            '<span class="node-region">' + node.region + '</span>' +
          '</span>' +
        '</span>' +
        '<span class="node-ping">' + node.ping + 'ms</span>';
      networkGrid.appendChild(card);
    });
  }

  /* ----------------------------------------
     FAQ accordion
  ---------------------------------------- */
  var accordion = document.getElementById("accordion");
  if (accordion) {
    accordion.querySelectorAll(".accordion-trigger").forEach(function (trigger) {
      trigger.addEventListener("click", function () {
        var panel = trigger.nextElementSibling;
        var isOpen = trigger.getAttribute("aria-expanded") === "true";

        accordion.querySelectorAll(".accordion-trigger").forEach(function (t) {
          t.setAttribute("aria-expanded", "false");
          t.nextElementSibling.style.maxHeight = null;
        });

        if (!isOpen) {
          trigger.setAttribute("aria-expanded", "true");
          panel.style.maxHeight = panel.scrollHeight + "px";
        }
      });
    });
  }

  /* ----------------------------------------
     Contact form -> mailto:
     No backend, so "sending" opens the visitor's
     default email app with the message pre-filled.
  ---------------------------------------- */
  var CONTACT_EMAIL = "hello@forgenode.io"; // <-- change to your real inbox

  var contactForm = document.getElementById("contactForm");
  var formStatus = document.getElementById("formStatus");

  if (contactForm) {
    contactForm.addEventListener("submit", function (e) {
      e.preventDefault();

      var name = document.getElementById("name").value.trim();
      var email = document.getElementById("email").value.trim();
      var interest = document.getElementById("interest").value;
      var message = document.getElementById("message").value.trim();
      var emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

      if (!name || !email || !message) {
        formStatus.textContent = "Please fill in every required field.";
        formStatus.classList.add("is-error");
        return;
      }
      if (!emailPattern.test(email)) {
        formStatus.textContent = "That email address doesn't look right.";
        formStatus.classList.add("is-error");
        return;
      }

      var subject = "New inquiry: " + interest + " (" + name + ")";
      var body =
        "Name: " + name + "\n" +
        "Email: " + email + "\n" +
        "Interest: " + interest + "\n\n" +
        message;

      var mailtoLink =
        "mailto:" + encodeURIComponent(CONTACT_EMAIL) +
        "?subject=" + encodeURIComponent(subject) +
        "&body=" + encodeURIComponent(body);

      window.location.href = mailtoLink;

      formStatus.classList.remove("is-error");
      formStatus.textContent = "Opening your email app to send this to " + CONTACT_EMAIL + "...";
      contactForm.reset();
    });
  }

  /* ----------------------------------------
     Back to top button
  ---------------------------------------- */
  var backToTop = document.getElementById("backToTop");
  if (backToTop) {
    window.addEventListener("scroll", function () {
      if (window.scrollY > 600) {
        backToTop.classList.add("is-visible");
      } else {
        backToTop.classList.remove("is-visible");
      }
    }, { passive: true });

    backToTop.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: prefersReducedMotion ? "auto" : "smooth" });
    });
  }

  /* ----------------------------------------
     Footer year
  ---------------------------------------- */
  var yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

})();
