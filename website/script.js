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
     Terminal boot animation
  ---------------------------------------- */
  var terminalBody = document.getElementById("terminalBody");

  var script = [
    { text: "$ dmesg | grep nodepad", cls: "line-prompt", pause: 400 },
    { text: "[    0.000000] NodePad carrier board v0.1 detected", cls: "line-ok", pause: 500 },
    { text: "[    0.234100] Radxa CM5: RK3588S2, 8-core, 8 GB LPDDR4X", cls: "line-muted", pause: 450 },
    { text: "[    0.312000] rtl8125bg: 2.5GbE NIC #2 at PCIe 2.1 x1", cls: "line-muted", pause: 400 },
    { text: "[    0.418000] nvme: M.2 M-key 2280 — Samsung 980 PRO 512GB", cls: "line-muted", pause: 500 },
    { text: "[    0.502000] usb: 4× USB 3.0 via GL3523 hub", cls: "line-muted", pause: 350 },
    { text: "[    0.589000] poe: MP8007 PD detected, 802.3at 25W", cls: "line-accent", pause: 450 },
    { text: "[    0.671000] pd: CH224K negotiated 20V @ 3A", cls: "line-muted", pause: 400 },
    { text: "[    1.200000] eth0: 1 GbE (CM5 native) — link up", cls: "line-ok", pause: 350 },
    { text: "[    1.200100] eth1: 2.5 GbE (RTL8125BG) — link up", cls: "line-ok", pause: 350 },
    { text: "[    1.847000] system: boot complete in 1.8s ✔", cls: "line-ok", pause: 1200 },
    { text: "$ kubectl get nodes", cls: "line-prompt", pause: 500 },
    { text: "NAME       STATUS   ROLES   AGE   VERSION", cls: "line-muted", pause: 200 },
    { text: "nodepad-1  Ready    worker  2d    v1.29.0", cls: "line-ok", pause: 200 },
    { text: "nodepad-2  Ready    worker  2d    v1.29.0", cls: "line-ok", pause: 200 },
    { text: "nodepad-3  Ready    control-plane  2d  v1.29.0", cls: "line-ok", pause: 200 },
    { text: "nodepad-4  Ready    worker  2d    v1.29.0", cls: "line-ok", pause: 2600 }
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
        return typeLine(terminalBody, line.text, line.cls, 14).then(function () {
          return new Promise(function (r) { setTimeout(r, line.pause); });
        });
      });
    });
    chain.then(function () {
      /* terminal done — do not loop */
    });
  }

  runTerminalScript();

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
  ---------------------------------------- */
  var CONTACT_EMAIL = "hello@nodepad.dev";
  var contactForm = document.getElementById("contactForm");
  var formStatus = document.getElementById("formStatus");

  if (contactForm) {
    contactForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var name = document.getElementById("name").value.trim();
      var email = document.getElementById("email").value.trim();
      var interest = document.getElementById("interest").value;
      var emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

      if (!name || !email) {
        formStatus.textContent = "Please fill in every required field.";
        formStatus.classList.add("is-error");
        return;
      }
      if (!emailPattern.test(email)) {
        formStatus.textContent = "That email address doesn't look right.";
        formStatus.classList.add("is-error");
        return;
      }

      var subject = "NodePad interest: " + interest + " (" + name + ")";
      var body = "Name: " + name + "\nEmail: " + email + "\nInterest: " + interest;
      var mailtoLink = "mailto:" + encodeURIComponent(CONTACT_EMAIL) + "?subject=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(body);
      window.location.href = mailtoLink;

      formStatus.classList.remove("is-error");
      formStatus.textContent = "Opening your email app...";
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

  /* ----------------------------------------
     Scroll reveal
  ---------------------------------------- */
  if (!prefersReducedMotion) {
    var revealEls = document.querySelectorAll(".feature, .variant-card, .pricing-card, .roadmap-item, .accordion-item");
    revealEls.forEach(function (el) { el.classList.add("reveal"); });

    var revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: "0px 0px -40px 0px" });

    revealEls.forEach(function (el) { revealObserver.observe(el); });
  }

  /* ----------------------------------------
     Three.js — PCB model that disassembles on scroll
  ---------------------------------------- */
  var canvasContainer = document.getElementById("heroCanvas");
  if (!canvasContainer || typeof THREE === "undefined" || prefersReducedMotion) return;

  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(45, canvasContainer.clientWidth / canvasContainer.clientHeight, 0.1, 1000);
  camera.position.set(0, 3, 8);
  camera.lookAt(0, 0.5, 0);

  var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(canvasContainer.clientWidth, canvasContainer.clientHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x000000, 0);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.1;
  renderer.outputEncoding = THREE.sRGBEncoding;
  canvasContainer.appendChild(renderer.domElement);

  /* Lights */
  var ambientLight = new THREE.AmbientLight(0xffffff, 0.35);
  scene.add(ambientLight);
  var dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
  dirLight.position.set(5, 10, 5);
  dirLight.castShadow = true;
  scene.add(dirLight);
  var fillLight = new THREE.DirectionalLight(0x88aaff, 0.3);
  fillLight.position.set(-5, 3, -3);
  scene.add(fillLight);
  var rimLight = new THREE.DirectionalLight(0x4f8dfd, 0.4);
  rimLight.position.set(0, -2, -5);
  scene.add(rimLight);
  var pointLight = new THREE.PointLight(0x2dd4a7, 0.5, 15);
  pointLight.position.set(-3, 5, 3);
  scene.add(pointLight);
  var warmLight = new THREE.PointLight(0xffaa44, 0.2, 10);
  warmLight.position.set(4, 2, -2);
  scene.add(warmLight);

  /* ---- Materials ---- */
  var pcbGreen = new THREE.MeshStandardMaterial({ color: 0x1a6b3c, roughness: 0.55, metalness: 0.15 });
  var copperMat = new THREE.MeshStandardMaterial({ color: 0xc87533, roughness: 0.3, metalness: 0.65 });
  var chipBlack = new THREE.MeshStandardMaterial({ color: 0x111118, roughness: 0.35, metalness: 0.25 });
  var chipDark = new THREE.MeshStandardMaterial({ color: 0x1a1a28, roughness: 0.4, metalness: 0.2 });
  var plasticBlack = new THREE.MeshStandardMaterial({ color: 0x1e1e2a, roughness: 0.6, metalness: 0.1 });
  var metalBrushed = new THREE.MeshStandardMaterial({ color: 0x999999, roughness: 0.3, metalness: 0.85 });
  var greenLedMat = new THREE.MeshStandardMaterial({ color: 0x2dd4a7, emissive: 0x2dd4a7, emissiveIntensity: 0.5, roughness: 0.3 });
  var heatsinkMat = new THREE.MeshStandardMaterial({ color: 0x2a2a36, roughness: 0.25, metalness: 0.7 });

  var components = [];

  function addComponent(mesh, explodeDir, explodeDelay) {
    mesh.userData.basePos = mesh.position.clone();
    mesh.userData.baseRot = mesh.rotation.clone();
    mesh.userData.explodeDir = explodeDir.normalize();
    mesh.userData.explodeDelay = explodeDelay || 0;
    scene.add(mesh);
    components.push(mesh);
    return mesh;
  }

  /* helper: box mesh shortcut */
  function B(w, h, d, mat) { return new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); }

  /* ============================================
     BOARD
     ============================================ */
  var BW = 5, BD = 5, BH = 0.12;
  var boardGeo = new THREE.BoxGeometry(BW, BH, BD);
  var board = addComponent(new THREE.Mesh(boardGeo, pcbGreen), new THREE.Vector3(0, -1, 0), 0.8);

  /* Traces */
  var traceMat = new THREE.MeshStandardMaterial({ color: 0xc87533, roughness: 0.3, metalness: 0.6 });
  [[0, 0.9, 0.04, 1.8, 0], [0, -0.9, 0.04, 1.8, 0], [-1, 0, 0.03, 3, Math.PI/2],
   [1, 0, 0.03, 3, Math.PI/2], [0.5, 1.5, 0.03, 1.2, Math.PI/4], [-0.5, -1.5, 0.03, 1.2, -Math.PI/4]
  ].forEach(function(t) {
    var m = B(t[2], 0.008, t[3], traceMat);
    m.position.set(t[0], BH/2 + 0.005, t[1]);
    m.rotation.y = t[4];
    board.add(m);
  });

  /* Mounting holes */
  [[-2.2, -2.2], [2.2, -2.2], [-2.2, 2.2], [2.2, 2.2]].forEach(function(p) {
    var hole = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, BH + 0.02, 12), new THREE.MeshStandardMaterial({ color: 0x060606 }));
    hole.position.set(p[0], 0, p[1]);
    board.add(hole);
  });

  /* ============================================
     COMPONENTS — logically placed
     ============================================
     Board layout (top view, z+ = front edge):
     ┌──────────────────────────────────────────┐
     │  RJ45#1   RJ45#2          [front edge]   │ z = +2.4
     │                                          │
     │  RTL8125    CM5 SoM        M.2 M-key     │ z = +1 .. -0.5
     │  +TCXO    (center)         NVMe          │
     │                                          │
     │  PoE xfmr   SoM conn      USB hub        │ z = -0.5 .. -1.5
     │  RTC+batt   SoM conn      M.2 E-key      │
     │                                          │
     │  LEDs   GPIO header   microSD  USB-C     │ z = -2 .. -2.4
     │                      HDMI  USB×4 [rear]  │
     └──────────────────────────────────────────┘
     x: -2.5 ─────────────────────────── +2.5
  */

  /* ---- CM5 SoM (center of board) ---- */
  var cm5 = addComponent((function() {
    var g = new THREE.Group();
    g.add(B(2.2, 0.06, 1.6, new THREE.MeshStandardMaterial({ color: 0x0e5e2e, roughness: 0.5, metalness: 0.15 })));
    var pkg = B(1.6, 0.12, 1.1, chipBlack); pkg.position.y = 0.09; g.add(pkg);
    var hs = B(1.9, 0.06, 1.3, heatsinkMat); hs.position.y = 0.18; g.add(hs);
    for (var fi = 0; fi < 8; fi++) {
      var fin = B(0.025, 0.1, 1.2, heatsinkMat); fin.position.set(-0.8 + fi * 0.22, 0.26, 0); g.add(fin);
    }
    return g;
  })(), new THREE.Vector3(0, 2.5, 0), 0);
  cm5.position.set(0, BH/2 + 0.03, 0);

  /* ---- SoM connectors (under CM5, north + south) ---- */
  var somC1 = addComponent(B(2.0, 0.1, 0.14, plasticBlack), new THREE.Vector3(0, 1.8, 1.5), 0.05);
  somC1.position.set(0, BH/2 + 0.05, 0.6);
  var somC2 = addComponent(B(2.0, 0.1, 0.14, plasticBlack), new THREE.Vector3(0, 1.8, -1.5), 0.08);
  somC2.position.set(0, BH/2 + 0.05, -0.6);

  /* ---- Dual RJ45 (front edge, left side) ---- */
  function makeRJ45() {
    var g = new THREE.Group();
    g.add(B(0.46, 0.5, 0.72, plasticBlack));
    var port = B(0.26, 0.2, 0.12, new THREE.MeshStandardMaterial({ color: 0x050505 }));
    port.position.z = 0.38; g.add(port);
    var shield = B(0.36, 0.3, 0.05, metalBrushed);
    shield.position.z = 0.36; g.add(shield);
    var ledG = B(0.04, 0.04, 0.04, greenLedMat); ledG.position.set(-0.1, 0.2, 0.36); g.add(ledG);
    var ledY = B(0.04, 0.04, 0.04, new THREE.MeshStandardMaterial({ color: 0xffcc00, emissive: 0xffcc00, emissiveIntensity: 0.3 }));
    ledY.position.set(0.1, 0.2, 0.36); g.add(ledY);
    return g;
  }
  var rj1 = addComponent(makeRJ45(), new THREE.Vector3(-1, 1.5, 3), 0.15);
  rj1.position.set(-1.2, BH/2 + 0.25, 2.3);
  var rj2 = addComponent(makeRJ45(), new THREE.Vector3(0, 1.5, 3), 0.2);
  rj2.position.set(-0.3, BH/2 + 0.25, 2.3);

  /* ---- RTL8125 + 25MHz TCXO (left of CM5) ---- */
  var nic = addComponent((function() {
    var g = new THREE.Group();
    g.add(B(0.5, 0.08, 0.5, chipDark));
    return g;
  })(), new THREE.Vector3(-2.5, 1.5, 0.5), 0.1);
  nic.position.set(-1.8, BH/2 + 0.04, 1.5);

  var tcxo = addComponent(B(0.1, 0.05, 0.07, metalBrushed), new THREE.Vector3(-2.5, 1.2, 1.2), 0.12);
  tcxo.position.set(-1.3, BH/2 + 0.03, 1.8);

  /* ---- M.2 M-key NVMe (right of CM5) ---- */
  var m2 = addComponent((function() {
    var g = new THREE.Group();
    g.add(B(0.32, 0.05, 1.8, plasticBlack));
    var notch = B(0.06, 0.06, 0.1, new THREE.MeshStandardMaterial({ color: 0x040404 }));
    notch.position.set(0.15, 0.01, -0.45); g.add(notch);
    var notch2 = notch.clone(); notch2.position.z = 0.45; g.add(notch2);
    return g;
  })(), new THREE.Vector3(2, 1.8, 0), 0.4);
  m2.position.set(1.8, BH/2 + 0.025, 0);

  /* ---- M.2 E-key WiFi (rear-left area) ---- */
  var m2e = addComponent(B(0.28, 0.04, 0.8, plasticBlack), new THREE.Vector3(-2, 1.8, -1.5), 0.45);
  m2e.position.set(-1.2, BH/2 + 0.02, -1.5);

  /* ---- USB hub GL3523 (between M.2 slots) ---- */
  var hub = addComponent(B(0.28, 0.07, 0.28, chipDark), new THREE.Vector3(1.5, 1.5, -1), 0.33);
  hub.position.set(0.8, BH/2 + 0.035, -0.8);

  /* ---- 4× USB-A 3.0 (rear edge, right side) ---- */
  function makeUSB3() {
    var g = new THREE.Group();
    g.add(B(0.28, 0.18, 0.5, metalBrushed));
    var tongue = B(0.18, 0.03, 0.32, new THREE.MeshStandardMaterial({ color: 0x1144aa, roughness: 0.5 }));
    tongue.position.set(0, -0.02, 0.05); g.add(tongue);
    return g;
  }
  for (var u = 0; u < 4; u++) {
    var ua = addComponent(makeUSB3(), new THREE.Vector3(2.5, 1, -1.5 + u * 0.38), 0.3 + u * 0.04);
    ua.position.set(2.35, BH/2 + 0.09, -1.5 + u * 0.38);
  }

  /* ---- HDMI (rear edge, left of USB) ---- */
  var hdmi = addComponent((function() {
    var g = new THREE.Group();
    g.add(B(0.52, 0.17, 0.58, metalBrushed));
    var port = B(0.36, 0.08, 0.1, new THREE.MeshStandardMaterial({ color: 0x060606 }));
    port.position.z = 0.3; g.add(port);
    return g;
  })(), new THREE.Vector3(1, 1.5, -3), 0.35);
  hdmi.position.set(0.8, BH/2 + 0.08, -2.3);

  /* ---- USB-C power (rear edge, far left) ---- */
  var usbc = addComponent((function() {
    var g = new THREE.Group();
    g.add(B(0.34, 0.12, 0.38, metalBrushed));
    var port = B(0.2, 0.06, 0.08, new THREE.MeshStandardMaterial({ color: 0x060606 }));
    port.position.z = 0.2; g.add(port);
    return g;
  })(), new THREE.Vector3(-1, 1.5, -3), 0.25);
  usbc.position.set(-0.8, BH/2 + 0.06, -2.3);

  /* ---- microSD (rear edge, near USB-C) ---- */
  var sd = addComponent(B(0.3, 0.12, 0.35, new THREE.MeshStandardMaterial({ color: 0x3a3a48, roughness: 0.55 })), new THREE.Vector3(-1.8, 1.5, -2.8), 0.22);
  sd.position.set(-1.5, BH/2 + 0.06, -2.2);

  /* ---- 40-pin GPIO header (rear edge, far right) ---- */
  var gpio = addComponent((function() {
    var g = new THREE.Group();
    g.add(B(1.6, 0.2, 0.24, plasticBlack));
    for (var p = 0; p < 20; p++) {
      var pin = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.15, 4), metalBrushed);
      pin.position.set(-0.74 + p * 0.078, 0.15, -0.035); g.add(pin);
      var pin2 = pin.clone(); pin2.position.z = 0.035; g.add(pin2);
    }
    return g;
  })(), new THREE.Vector3(0, 2, -3), 0.5);
  gpio.position.set(-0.2, BH/2 + 0.1, -2.3);

  /* ---- PoE transformer (front-left area) ---- */
  var poe = addComponent(B(0.4, 0.3, 0.4, new THREE.MeshStandardMaterial({ color: 0x2d2d2d, roughness: 0.6 })), new THREE.Vector3(-2.5, 1.5, 2.5), 0.55);
  poe.position.set(-2, BH/2 + 0.15, 1.8);

  /* ---- Power section: inductor + caps (front-right) ---- */
  var inductor = addComponent(B(0.35, 0.16, 0.35, new THREE.MeshStandardMaterial({ color: 0x2a2a2a, roughness: 0.4, metalness: 0.5 })), new THREE.Vector3(2.5, 1.8, 2), 0.6);
  inductor.position.set(1.8, BH/2 + 0.08, 1.8);

  /* Electrolytic caps near power */
  [[2.0, 1.3], [1.4, 1.8]].forEach(function(cp) {
    var cap = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.1, 8), new THREE.MeshStandardMaterial({ color: 0x1a1a6a, roughness: 0.5 }));
    cap.position.set(cp[0], BH/2 + 0.05, cp[1]);
    board.add(cap);
  });

  /* ---- CH224K PD trigger (near USB-C) ---- */
  var ch224 = addComponent(B(0.12, 0.05, 0.08, chipDark), new THREE.Vector3(-1, 1.2, -2), 0.28);
  ch224.position.set(-1.2, BH/2 + 0.025, -1.8);

  /* ---- DS3231 RTC + CR2032 (left edge, center) ---- */
  var rtc = addComponent((function() {
    var g = new THREE.Group();
    g.add(B(0.2, 0.07, 0.16, chipDark));
    var holder = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 0.05, 12), metalBrushed);
    holder.position.set(0.28, 0.01, 0); g.add(holder);
    var batt = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.13, 0.025, 12), new THREE.MeshStandardMaterial({ color: 0xc0c0c0, roughness: 0.2, metalness: 0.8 }));
    batt.position.set(0.28, 0.04, 0); g.add(batt);
    return g;
  })(), new THREE.Vector3(-2.5, 1.5, -0.5), 0.65);
  rtc.position.set(-2, BH/2 + 0.035, -0.8);

  /* ---- Status LEDs (front-left corner) ---- */
  var ledColors = [greenLedMat, greenLedMat, new THREE.MeshStandardMaterial({ color: 0xff5555, emissive: 0xff5555, emissiveIntensity: 0.4 }), greenLedMat, new THREE.MeshStandardMaterial({ color: 0x4f8dfd, emissive: 0x4f8dfd, emissiveIntensity: 0.4 })];
  ledColors.forEach(function(mat, i) {
    var led = addComponent(B(0.06, 0.05, 0.04, mat), new THREE.Vector3(-2 + i * 0.15, 2, 2.5), 0.7 + i * 0.03);
    led.position.set(-2.2 + i * 0.15, BH/2 + 0.025, -2.2);
  });

  /* ---- Reset + Boot buttons (left edge) ---- */
  function makeBtn() {
    var g = new THREE.Group();
    g.add(B(0.12, 0.07, 0.12, plasticBlack));
    var cap = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.03, 8), metalBrushed);
    cap.position.y = 0.05; g.add(cap);
    return g;
  }
  var btn1 = addComponent(makeBtn(), new THREE.Vector3(-2.5, 1.5, -1.5), 0.68);
  btn1.position.set(-2.2, BH/2 + 0.035, -1.5);
  var btn2 = addComponent(makeBtn(), new THREE.Vector3(-2.5, 1.5, -1.8), 0.7);
  btn2.position.set(-2.2, BH/2 + 0.035, -1.8);

  /* ---- MP2315 + AP2112K (near power section) ---- */
  var buck = addComponent(B(0.1, 0.04, 0.07, chipDark), new THREE.Vector3(2, 1.5, 1.5), 0.62);
  buck.position.set(1.4, BH/2 + 0.02, 1.5);
  var ldo = addComponent(B(0.08, 0.04, 0.05, chipDark), new THREE.Vector3(2, 1.5, 1.7), 0.63);
  ldo.position.set(1.6, BH/2 + 0.02, 1.5);

  /* ---- SMD passives (clustered near real components) ---- */
  [[-0.7, 0.5], [-0.5, 0.5], [0.5, 0.5], [0.7, 0.5], [-0.7, -0.5], [-0.5, -0.5], [0.5, -0.5], [0.7, -0.5],
   [-1.5, 1.2], [-1.3, 1.2], [-2, 1.2],
   [1.5, 1.5], [1.3, 1.5], [2, 1.5],
   [-0.9, 2.0], [-0.5, 2.0], [0.0, 2.0],
   [-1.5, -1.2], [1.0, -1.5], [-0.5, -1.8],
  ].forEach(function(sp) {
    var smd = B(0.05, 0.02, 0.025, chipDark);
    smd.position.set(sp[0], BH/2 + 0.01, sp[1]);
    smd.rotation.y = Math.random() > 0.5 ? 0 : Math.PI / 2;
    board.add(smd);
  });

  /* Initial rotation */
  var boardGroup = new THREE.Group();
  scene.remove(board);
  boardGroup.add(board);
  components.forEach(function (c) {
    if (c !== board) {
      scene.remove(c);
      boardGroup.add(c);
    }
  });
  scene.add(boardGroup);
  boardGroup.rotation.x = -0.3;
  boardGroup.rotation.y = 0.6;

  /* Scroll tracking — disassembly spans the entire page */
  var scrollProgress = 0;

  function getScrollProgress() {
    var scrolled = window.scrollY;
    var docH = document.documentElement.scrollHeight - window.innerHeight;
    if (docH <= 0) return 0;
    return Math.max(0, Math.min(1, scrolled / docH));
  }

  /* Mouse parallax */
  var mouseX = 0, mouseY = 0;
  var targetMouseX = 0, targetMouseY = 0;
  document.addEventListener("mousemove", function (e) {
    targetMouseX = (e.clientX / window.innerWidth - 0.5) * 2;
    targetMouseY = (e.clientY / window.innerHeight - 0.5) * 2;
  }, { passive: true });

  /* Hero overlay — fades out as user scrolls */
  var heroOverlay = document.querySelector(".hero-overlay");
  var heroSection = document.querySelector(".hero");

  /* Animation loop */
  var startTime = Date.now();

  function animate() {
    requestAnimationFrame(animate);

    scrollProgress = getScrollProgress();
    mouseX += (targetMouseX - mouseX) * 0.05;
    mouseY += (targetMouseY - mouseY) * 0.05;

    /* Slow idle spin when at top, blends into scroll-driven rotation */
    var elapsed = (Date.now() - startTime) / 1000;
    var idleSpin = (1 - scrollProgress) * elapsed * 0.15;

    /* Rotate based on mouse + scroll + idle spin */
    var baseRotY = 0.6 + mouseX * 0.15 + idleSpin;
    var baseRotX = -0.3 + mouseY * 0.1;
    boardGroup.rotation.y = baseRotY + scrollProgress * 1.2;
    boardGroup.rotation.x = baseRotX - scrollProgress * 0.4;

    /* Disassemble components */
    components.forEach(function (comp) {
      if (comp === board) return;
      var delay = comp.userData.explodeDelay;
      var localProgress = Math.max(0, (scrollProgress - delay) / (1 - delay));
      localProgress = Math.min(1, localProgress);

      /* Ease out */
      var eased = 1 - Math.pow(1 - localProgress, 3);

      var dir = comp.userData.explodeDir;
      var base = comp.userData.basePos;
      var dist = 3.5 * eased;

      comp.position.x = base.x + dir.x * dist;
      comp.position.y = base.y + dir.y * dist;
      comp.position.z = base.z + dir.z * dist;

      /* Slight rotation during explosion */
      comp.rotation.x = comp.userData.baseRot.x + eased * 0.3 * (dir.z > 0 ? 1 : -1);
      comp.rotation.z = comp.userData.baseRot.z + eased * 0.2 * (dir.x > 0 ? 1 : -1);
    });

    /* Board sinks down slightly */
    board.position.y = board.userData.basePos.y - scrollProgress * 0.5;

    /* Scale down the whole assembly as it explodes */
    var scale = 1 - scrollProgress * 0.2;
    boardGroup.scale.set(scale, scale, scale);

    /* Camera adjusts */
    camera.position.y = 3 + scrollProgress * 1.5;
    camera.position.z = 8 - scrollProgress * 2;
    camera.lookAt(0, 0.5 + scrollProgress * 0.5, 0);

    /* Fade hero overlay so 3D model stays visible beneath page content */
    if (heroOverlay && heroSection) {
      var heroH = heroSection.offsetHeight;
      var heroFade = Math.max(0, Math.min(1, window.scrollY / (heroH * 0.5)));
      heroOverlay.style.opacity = 1 - heroFade * 0.7;
    }

    renderer.render(scene, camera);
  }

  animate();

  /* Resize */
  window.addEventListener("resize", function () {
    if (!canvasContainer) return;
    var w = canvasContainer.clientWidth;
    var h = canvasContainer.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  }, { passive: true });

})();
