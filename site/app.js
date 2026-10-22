(() => {
  const navigation = performance.getEntriesByType?.("navigation")[0];
  const isReload = navigation?.type === "reload";

  function jumpTo(target) {
    const root = document.documentElement;
    const previous = root.style.scrollBehavior;
    root.style.scrollBehavior = "auto";
    target.scrollIntoView();
    root.style.scrollBehavior = previous;
  }

  function placeOnLoad() {
    if (location.hash) {
      const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
      if (target) {
        jumpTo(target);
        return;
      }
    }
    if (isReload) window.scrollTo(0, 0);
  }

  placeOnLoad();
  window.addEventListener("pageshow", placeOnLoad);
  window.addEventListener("load", placeOnLoad);

  const themeToggle = document.querySelector("[data-theme-toggle]");
  const navToggle = document.querySelector("[data-nav-toggle]");
  const siteNav = document.querySelector(".site-nav");

  function closeNavigation() {
    navToggle?.setAttribute("aria-expanded", "false");
    navToggle?.setAttribute("aria-label", "Open navigation");
    navToggle?.setAttribute("title", "Open navigation");
    siteNav?.classList.remove("is-open");
  }

  navToggle?.addEventListener("click", () => {
    const isOpen = navToggle.getAttribute("aria-expanded") === "true";
    navToggle.setAttribute("aria-expanded", String(!isOpen));
    navToggle.setAttribute("aria-label", isOpen ? "Open navigation" : "Close navigation");
    navToggle.setAttribute("title", isOpen ? "Open navigation" : "Close navigation");
    siteNav?.classList.toggle("is-open", !isOpen);
  });

  siteNav?.addEventListener("click", (event) => {
    if (event.target.closest("a")) closeNavigation();
  });

  document.addEventListener("click", (event) => {
    if (!siteNav?.classList.contains("is-open")) return;
    if (event.target.closest("[data-nav-toggle], .site-nav")) return;
    closeNavigation();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && siteNav?.classList.contains("is-open")) {
      closeNavigation();
      navToggle?.focus();
    }
  });

  const themeMedia = window.matchMedia?.("(prefers-color-scheme: dark)");
  let storedTheme = null;
  try {
    storedTheme = localStorage.getItem("sarawak-theme");
  } catch (error) {}

  function setTheme(theme, persist = false) {
    const isDark = theme === "dark";
    if (isDark) document.documentElement.setAttribute("data-theme", "dark");
    else document.documentElement.removeAttribute("data-theme");
    if (persist) {
      try {
        localStorage.setItem("sarawak-theme", isDark ? "dark" : "light");
      } catch (error) {}
    }
    if (themeToggle) {
      const nextLabel = isDark ? "Switch to light mode" : "Switch to dark mode";
      themeToggle.setAttribute("aria-label", nextLabel);
      themeToggle.setAttribute("title", nextLabel);
      themeToggle.setAttribute("aria-pressed", String(isDark));
    }
  }

  setTheme(document.documentElement.hasAttribute("data-theme") ? "dark" : "light");
  themeToggle?.addEventListener("click", () => {
    setTheme(document.documentElement.hasAttribute("data-theme") ? "light" : "dark", true);
  });
  if (!storedTheme && themeMedia) {
    themeMedia.addEventListener?.("change", (event) => setTheme(event.matches ? "dark" : "light"));
  }

/* sn-kit:back-to-top:begin */
  const backToTop = document.querySelector("[data-back-to-top]");
  if (backToTop) {
    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    let hideTimer = 0;

    function updateBackToTop() {
      const show = window.scrollY >= 600;
      const reduce = Boolean(reduceMotion?.matches);
      if (show) {
        window.clearTimeout(hideTimer);
        backToTop.hidden = false;
        if (reduce) backToTop.classList.add("is-visible");
        else requestAnimationFrame(() => {
          if (window.scrollY >= 600) backToTop.classList.add("is-visible");
        });
        return;
      }
      backToTop.classList.remove("is-visible");
      if (reduce || backToTop.hidden) {
        backToTop.hidden = true;
        return;
      }
      window.clearTimeout(hideTimer);
      hideTimer = window.setTimeout(() => {
        if (window.scrollY < 600) backToTop.hidden = true;
      }, 200);
    }

    backToTop.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: reduceMotion?.matches ? "auto" : "smooth" });
    });
    window.addEventListener("scroll", updateBackToTop, { passive: true });
    updateBackToTop();
  }
/* sn-kit:back-to-top:end */
  function bindCategoryScrollHint(filter) {
    const wrap = filter.querySelector("[data-category-scroll]");
    const scroller = wrap?.querySelector(".category-filter-options");
    if (!wrap || !scroller) return;

    const update = () => {
      const overflow = scroller.scrollWidth - scroller.clientWidth;
      const overflows = overflow > 1;
      wrap.classList.toggle("can-scroll-start", overflows && scroller.scrollLeft > 1);
      wrap.classList.toggle("can-scroll-end", overflows && scroller.scrollLeft < overflow - 1);
    };

    scroller.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    if (typeof ResizeObserver !== "undefined") {
      const observer = new ResizeObserver(update);
      observer.observe(scroller);
    }
    update();
    document.fonts?.ready?.then(update);
  }

  const filter = document.querySelector("[data-category-filter]");
  if (filter) {
    const buttons = Array.from(filter.querySelectorAll("[data-section-filter]"));
    const groups = Array.from(document.querySelectorAll(".group"));
    const status = filter.querySelector("[data-filter-status]");

    function applyFilter(section) {
      const activeButton = buttons.find((button) => button.dataset.sectionFilter === section);
      if (!activeButton) return;

      let visibleCount = 0;
      groups.forEach((group) => {
        const isVisible = section === "all" || group.id === section;
        group.hidden = !isVisible;
        if (isVisible) visibleCount += group.querySelectorAll(".scheme").length;
      });

      buttons.forEach((button) => {
        const isActive = button === activeButton;
        button.classList.toggle("is-active", isActive);
        button.setAttribute("aria-pressed", String(isActive));
      });

      if (status) {
        status.textContent = section === "all"
          ? `Showing all ${visibleCount} schemes`
          : `Showing ${visibleCount} ${activeButton.dataset.filterLabel} schemes`;
      }
    }

    filter.addEventListener("click", (event) => {
      const button = event.target.closest("[data-section-filter]");
      if (!button || !filter.contains(button)) return;
      const resetToAll = button.classList.contains("is-active") && button.dataset.sectionFilter !== "all";
      applyFilter(resetToAll ? "all" : button.dataset.sectionFilter);
    });

    document.addEventListener("click", (event) => {
      const link = event.target.closest("a[href*='#']");
      if (!link) return;
      const href = link.getAttribute("href") || "";
      const hashIndex = href.indexOf("#");
      if (hashIndex === -1) return;
      const id = decodeURIComponent(href.slice(hashIndex + 1));
      if (!buttons.some((button) => button.dataset.sectionFilter === id)) return;
      event.preventDefault();
      applyFilter(id);
      const target = document.getElementById(id);
      if (!target) return;
      history.pushState(null, "", `#${id}`);
      jumpTo(target);
    });

    const fromHash = location.hash ? decodeURIComponent(location.hash.slice(1)) : "";
    applyFilter(buttons.some((button) => button.dataset.sectionFilter === fromHash) ? fromHash : "all");
    bindCategoryScrollHint(filter);
  }

  const schemeCards = document.querySelectorAll(".scheme");
  const reduceSchemeMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
  if (schemeCards.length && !reduceSchemeMotion && "IntersectionObserver" in window) {
    const schemeObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-revealed");
        schemeObserver.unobserve(entry.target);
      });
    }, { rootMargin: "0px", threshold: 0 });
    schemeCards.forEach((card) => schemeObserver.observe(card));
  }
})();
