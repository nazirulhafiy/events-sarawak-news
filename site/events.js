(() => {
  const tabs = document.querySelector("[data-months]");
  if (!tabs) return;
  const panels = document.querySelectorAll("[data-panel]");
  const heading = document.querySelector("[data-month-heading]");
  const FULL = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  const VALID_TYPES = new Set(["festival", "sports", "cultural", "concert"]);
  const params = new URLSearchParams(location.search);
  const typeParam = (params.get("event_type") || "").toLowerCase();
  const activeType = VALID_TYPES.has(typeParam) ? typeParam : null;

  function mytMonth() {
    const parts = new Intl.DateTimeFormat("en-GB", { timeZone: "Asia/Kuching", month: "numeric", year: "numeric" }).formatToParts(new Date());
    const y = +parts.find(p => p.type === "year").value, m = +parts.find(p => p.type === "month").value;
    return y < 2026 ? 1 : y > 2026 ? 12 : m;
  }

  function visibleCount(panel) {
    return [...panel.querySelectorAll(".event-card")].filter(c => !c.hidden).length;
  }

  function applyTypeFilter() {
    panels.forEach(panel => {
      panel.querySelectorAll(".event-card").forEach(card => {
        card.hidden = !!(activeType && card.dataset.eventType !== activeType);
      });
      let note = panel.querySelector("[data-type-filter-empty]");
      const n = visibleCount(panel);
      const hasCards = panel.querySelector(".event-card");
      if (activeType && hasCards && n === 0) {
        if (!note) {
          note = document.createElement("li");
          note.className = "event-empty";
          note.dataset.typeFilterEmpty = "";
          panel.appendChild(note);
        }
        const label = activeType.charAt(0).toUpperCase() + activeType.slice(1);
        const month = FULL[+panel.dataset.panel - 1];
        note.textContent = `No ${label} events listed for ${month} yet.`;
        note.hidden = false;
      } else if (note) {
        note.hidden = true;
      }
    });
    tabs.querySelectorAll("[data-m]").forEach(b => {
      const panel = document.getElementById(`panel-${b.dataset.m}`);
      if (!panel) return;
      const n = visibleCount(panel);
      let badge = b.querySelector(".category-filter-count");
      if (activeType) {
        if (n) {
          if (!badge) {
            badge = document.createElement("span");
            badge.className = "category-filter-count";
            badge.setAttribute("aria-hidden", "true");
            b.appendChild(document.createTextNode(" "));
            b.appendChild(badge);
          }
          badge.textContent = String(n);
          badge.hidden = false;
        } else if (badge) {
          badge.remove();
        }
      }
      const month = FULL[+b.dataset.m - 1];
      b.setAttribute("aria-label", `${month}, ${n} event${n === 1 ? "" : "s"}`);
    });
  }

  function firstMonthWithEvents() {
    for (let m = 1; m <= 12; m++) {
      const panel = document.getElementById(`panel-${m}`);
      if (panel && visibleCount(panel) > 0) return m;
    }
    return null;
  }

  function select(m, focus) {
    tabs.querySelectorAll("[data-m]").forEach(b => {
      const on = +b.dataset.m === m;
      b.classList.toggle("is-active", on);
      b.setAttribute("aria-selected", String(on));
      b.tabIndex = on ? 0 : -1;
      if (on && focus) b.focus();
    });
    panels.forEach(p => { p.hidden = +p.dataset.panel !== m; });
    if (heading) heading.textContent = `${FULL[m - 1]} 2026`;
    const a = tabs.querySelector(".is-active");
    if (a) {
      const sc = tabs.scrollWidth > tabs.clientWidth ? tabs : (tabs.closest("[data-category-scroll]") || tabs);
      const ar = a.getBoundingClientRect(), sr = sc.getBoundingClientRect();
      sc.scrollLeft += ar.left - sr.left - (sr.width - ar.width) / 2;
    }
  }

  applyTypeFilter();
  const q = Number(params.get("month"));
  let month = q >= 1 && q <= 12 ? q : mytMonth();
  if (activeType && visibleCount(document.getElementById(`panel-${month}`)) === 0) {
    const first = firstMonthWithEvents();
    if (first) month = first;
  }
  select(month);

  tabs.addEventListener("click", ev => { const b = ev.target.closest("[data-m]"); if (b) select(+b.dataset.m); });
  tabs.addEventListener("keydown", ev => {
    const cur = +tabs.querySelector(".is-active").dataset.m;
    if (ev.key === "ArrowRight") select(cur % 12 + 1, true);
    else if (ev.key === "ArrowLeft") select((cur + 10) % 12 + 1, true);
    else return;
    ev.preventDefault();
  });

  // Whole-card click-through, same pattern as ai.sarawak.news .story-card.
  document.querySelectorAll(".event-card").forEach(card => {
    const link = card.querySelector(".event-link");
    if (!link) return;
    card.addEventListener("click", event => {
      if (event.target.closest("a, button, input, select, textarea")) return;
      link.click();
    });
    card.addEventListener("keydown", event => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      link.click();
    });
  });

  // Card reveal: same IntersectionObserver + is-revealed as bantuan.sarawak.news.
  const eventCards = document.querySelectorAll(".event-card");
  const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
  if (eventCards.length && !reduceMotion && "IntersectionObserver" in window) {
    const revealObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-revealed");
        revealObserver.unobserve(entry.target);
      });
    }, { rootMargin: "0px", threshold: 0 });
    eventCards.forEach(card => revealObserver.observe(card));
  }
})();
