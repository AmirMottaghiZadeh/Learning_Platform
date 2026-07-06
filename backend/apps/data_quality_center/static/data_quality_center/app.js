(function () {
  const key = "dq-theme";
  const root = document.documentElement;
  const saved = localStorage.getItem(key);
  if (saved === "dark" || saved === "light") {
    root.setAttribute("data-theme", saved);
  }
  const button = document.querySelector("[data-theme-toggle]");
  if (button) {
    button.addEventListener("click", () => {
      const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      localStorage.setItem(key, next);
    });
  }

  const selectAll = document.querySelector("[data-select-all]");
  if (selectAll) {
    selectAll.addEventListener("change", (event) => {
      document.querySelectorAll("input[data-bulk-select]").forEach((input) => {
        input.checked = event.target.checked;
      });
    });
  }
})();
