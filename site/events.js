(() => {
  const tabs = document.querySelector("[data-months]");
  if (!tabs) return;
  const panels = document.querySelectorAll("[data-panel]");
  const heading = document.querySelector("[data-month-heading]");
  const FULL = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  function mytMonth() {
    const parts = new Intl.DateTimeFormat("en-GB", { timeZone: "Asia/Kuching", month: "numeric", year: "numeric" }).formatToParts(new Date());
    const y = +parts.find(p => p.type === "year").value, m = +parts.find(p => p.type === "month").value;
    return y < 2026 ? 1 : y > 2026 ? 12 : m;
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
    const a = tabs.querySelector(".is-active"), sc = tabs.closest("[data-category-scroll]") || tabs;
    if (a) sc.scrollLeft = a.offsetLeft - sc.clientWidth / 2 + a.clientWidth / 2;
  }
  const q = Number(new URLSearchParams(location.search).get("month"));
  select(q >= 1 && q <= 12 ? q : mytMonth());
  tabs.addEventListener("click", ev => { const b = ev.target.closest("[data-m]"); if (b) select(+b.dataset.m); });
  tabs.addEventListener("keydown", ev => {
    const cur = +tabs.querySelector(".is-active").dataset.m;
    if (ev.key === "ArrowRight") select(cur % 12 + 1, true);
    else if (ev.key === "ArrowLeft") select((cur + 10) % 12 + 1, true);
    else return;
    ev.preventDefault();
  });
})();
