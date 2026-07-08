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
     Toast helper
  ---------------------------------------- */
  var toastEl = document.getElementById("toast");
  var toastTimer;
  function showToast(msg) {
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.classList.add("is-visible");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove("is-visible"); }, 3000);
  }

  /* ----------------------------------------
     Copy-to-clipboard helper
  ---------------------------------------- */
  function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        showToast("Copied: " + text);
      });
    } else {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      showToast("Copied: " + text);
    }
  }

  /* ----------------------------------------
     Variant "Get notified" -> scroll to CTA
  ---------------------------------------- */
  document.querySelectorAll(".notify-btn").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      var el = document.getElementById("emailSelect");
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
        setTimeout(function () { el.select && window.getSelection().selectAllChildren(el); }, 600);
      }
    });
  });

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
     Three.js — Real PCB model from KiCad GLB
  ---------------------------------------- */
  var canvasContainer = document.getElementById("heroCanvas");
  if (!canvasContainer || typeof THREE === "undefined" || typeof THREE.GLTFLoader === "undefined" || prefersReducedMotion) return;

  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(45, canvasContainer.clientWidth / canvasContainer.clientHeight, 0.1, 1000);
  camera.position.set(0, 3, 8);
  camera.lookAt(0, 0.5, 0);

  var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
  renderer.setSize(canvasContainer.clientWidth, canvasContainer.clientHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x000000, 0);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.3;
  renderer.outputEncoding = THREE.sRGBEncoding;
  canvasContainer.appendChild(renderer.domElement);

  /* Lights */
  scene.add(new THREE.AmbientLight(0xffffff, 0.3));
  var keyLight = new THREE.DirectionalLight(0xffeedd, 1.0);
  keyLight.position.set(6, 12, 8);
  scene.add(keyLight);
  scene.add(new THREE.DirectionalLight(0x8899cc, 0.4).translateX(-6).translateY(5).translateZ(-4));
  scene.add(new THREE.DirectionalLight(0x4488ff, 0.5).translateX(-2).translateY(3).translateZ(-8));
  scene.add(new THREE.PointLight(0x2dd4a7, 0.5, 12).translateY(-3));
  scene.add(new THREE.PointLight(0xffeedd, 0.2, 10).translateX(4).translateY(2));

  /* Load real PCB model */
  var boardGroup = new THREE.Group();
  scene.add(boardGroup);
  var components = [];
  var modelReady = false;

  var loader = new THREE.GLTFLoader();
  loader.load("nodepad.glb", function (gltf) {
    var model = gltf.scene;

    /* Center and scale the model */
    var box = new THREE.Box3().setFromObject(model);
    var center = box.getCenter(new THREE.Vector3());
    var size = box.getSize(new THREE.Vector3());
    var maxDim = Math.max(size.x, size.y, size.z);
    var scale = 5 / maxDim;
    model.scale.set(scale, scale, scale);
    model.position.sub(center.multiplyScalar(scale));

    boardGroup.add(model);

    /* Collect child meshes for disassembly */
    model.traverse(function (child) {
      if (child.isMesh) {
        child.userData.basePos = child.position.clone();
        child.userData.baseRot = child.rotation.clone();
        /* Explode direction = outward from center */
        var dir = child.position.clone().normalize();
        if (dir.length() < 0.01) dir.set(0, 1, 0);
        child.userData.explodeDir = dir;
        child.userData.explodeDelay = Math.random() * 0.5;
        components.push(child);
      }
    });

    modelReady = true;
  }, undefined, function (err) {
    console.warn("GLB load failed:", err);
  });

  /* Board rotation */
  boardGroup.rotation.x = -0.3;
  boardGroup.rotation.y = 0.6;

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
    boardGroup.rotation.y = baseRotY + scrollProgress * 0.4;
    boardGroup.rotation.x = baseRotX - scrollProgress * 0.15;

    /* Disassemble components */
    if (modelReady) components.forEach(function (comp) {
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
