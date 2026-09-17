(function () {
  "use strict";

  const THOUSANDS = /\B(?=(\d{3})+(?!\d))/g;

  function formatRupiah(digits) {
    return digits.replace(THOUSANDS, ".");
  }

  function initAlert(el) {
    setTimeout(function () {
      el.style.transition = "opacity .4s ease";
      el.style.opacity = "0";
      setTimeout(function () {
        el.remove();
      }, 400);
    }, 5000);
  }

  function initMoneyInput(input) {
    if (input.value) {
      const existing = parseFloat(input.value);
      input.value = isNaN(existing) ? "" : formatRupiah(String(Math.round(existing)));
    }

    input.addEventListener("input", function () {
      const caretFromEnd = input.value.length - input.selectionStart;
      input.value = formatRupiah(input.value.replace(/\D/g, ""));
      const caret = Math.max(input.value.length - caretFromEnd, 0);
      input.setSelectionRange(caret, caret);
    });

    if (input.form) {
      input.form.addEventListener("submit", function () {
        input.value = input.value.replace(/\D/g, "");
      });
    }
  }

  // ── Segmented control (pemilih tipe) — meng-enhance <select> native ──
  function initSegmented() {
    document.querySelectorAll("[data-segmented]").forEach(function (root) {
      const select = root.querySelector("[data-segmented-select]");
      const control = root.querySelector("[data-segmented-control]");
      const options = Array.from(root.querySelectorAll("[data-segmented-option]"));
      if (!select || !control || !options.length) return;

      select.classList.add("hidden");
      control.classList.remove("hidden");
      control.classList.add("grid");

      function paint() {
        options.forEach(function (btn) {
          const active = btn.getAttribute("data-segmented-option") === select.value;
          const activeCls = (btn.getAttribute("data-active-class") || "").split(/\s+/).filter(Boolean);
          const inactiveCls = (btn.getAttribute("data-inactive-class") || "").split(/\s+/).filter(Boolean);
          btn.setAttribute("aria-selected", active ? "true" : "false");
          if (active) {
            btn.classList.remove.apply(btn.classList, inactiveCls);
            btn.classList.add.apply(btn.classList, activeCls);
          } else {
            btn.classList.remove.apply(btn.classList, activeCls);
            btn.classList.add.apply(btn.classList, inactiveCls);
          }
        });
      }

      options.forEach(function (btn) {
        btn.addEventListener("click", function () {
          select.value = btn.getAttribute("data-segmented-option");
          paint();
          select.dispatchEvent(new Event("change", { bubbles: true }));
        });
      });

      paint();
    });
  }

  // ── Field dinamis per tipe transaksi + filter kategori ──
  function initTypeFields() {
    const form = document.querySelector("[data-transaction-form]");
    if (!form) return;
    const select = form.querySelector("[data-segmented-select]");
    if (!select) return;

    const fields = Array.from(form.querySelectorAll("[data-type-field]"));
    const accountField = form.querySelector("[data-account-field]");
    const comboboxes = Array.from(form.querySelectorAll("[data-combobox]"));

    function apply() {
      const type = select.value;

      fields.forEach(function (el) {
        const types = (el.getAttribute("data-type-field") || "").split(/\s+/);
        el.toggleAttribute("hidden", types.indexOf(type) === -1);
      });

      // Bersihkan akun tujuan saat bukan transfer agar tidak ikut terkirim.
      if (type !== "transfer") {
        const accountTo = form.querySelector("[name='account_to_id']");
        if (accountTo) accountTo.value = "";
      }

      if (accountField) {
        const label = accountField.querySelector("label");
        if (label) {
          label.textContent =
            type === "transfer"
              ? accountField.getAttribute("data-label-transfer") || "Akun"
              : accountField.getAttribute("data-label-default") || "Akun";
        }
      }

      comboboxes.forEach(function (root) {
        root.setAttribute("data-kind-filter", type === "transfer" ? "" : type);
        const input = root.querySelector("[data-combobox-input]");
        const native = root.querySelector("[data-combobox-native]");
        const menu = root.querySelector("[data-combobox-menu]");
        if (input) {
          input.value = "";
          input.setAttribute("aria-expanded", "false");
        }
        if (native) native.value = "";
        if (menu) menu.classList.add("hidden");
        root.classList.remove("is-open");
      });
    }

    select.addEventListener("change", apply);
    apply();
  }

  // ── Combobox: dropdown kategori yang bisa diketik untuk memfilter ──
  function initCombobox(root) {
    const select = root.querySelector("[data-combobox-native]");
    const control = root.querySelector("[data-combobox-control]");
    const input = root.querySelector("[data-combobox-input]");
    const menu = root.querySelector("[data-combobox-menu]");
    const empty = root.querySelector("[data-combobox-empty]");
    const options = Array.from(root.querySelectorAll("[data-combobox-option]"));
    if (!select || !control || !input || !menu) return;

    select.classList.add("hidden");
    control.classList.remove("hidden");

    const selected = select.options[select.selectedIndex];
    if (select.value && selected) input.value = selected.textContent.trim();

    let activeIndex = -1;

    function matches(opt) {
      const kind = root.getAttribute("data-kind-filter") || "";
      const query = input.value.trim().toLowerCase();
      const matchKind = !kind || opt.getAttribute("data-kind") === kind;
      const matchQuery = !query || opt.textContent.toLowerCase().indexOf(query) !== -1;
      return matchKind && matchQuery;
    }

    function applyFilter() {
      let shown = 0;
      options.forEach(function (opt) {
        const visible = matches(opt);
        opt.classList.toggle("hidden", !visible);
        opt.setAttribute("aria-selected", "false");
        opt.classList.remove("bg-surface");
        if (visible) shown += 1;
      });
      if (empty) empty.classList.toggle("hidden", shown !== 0);
      activeIndex = -1;
    }

    function highlight(visibleList) {
      options.forEach(function (opt) {
        opt.classList.remove("bg-surface");
      });
      if (activeIndex >= 0 && visibleList[activeIndex]) {
        visibleList[activeIndex].classList.add("bg-surface");
        visibleList[activeIndex].scrollIntoView({ block: "nearest" });
      }
    }

    function open() {
      applyFilter();
      menu.classList.remove("hidden");
      root.classList.add("is-open");
      input.setAttribute("aria-expanded", "true");
    }

    function close() {
      menu.classList.add("hidden");
      root.classList.remove("is-open");
      input.setAttribute("aria-expanded", "false");
    }

    function choose(opt) {
      options.forEach(function (o) {
        o.setAttribute("aria-selected", "false");
      });
      opt.setAttribute("aria-selected", "true");
      select.value = opt.getAttribute("data-value");
      input.value = opt.textContent.trim();
      close();
      select.dispatchEvent(new Event("change", { bubbles: true }));
    }

    input.addEventListener("focus", open);
    input.addEventListener("input", open);

    input.addEventListener("keydown", function (event) {
      const visibleList = options.filter(function (opt) {
        return !opt.classList.contains("hidden");
      });

      if (event.key === "ArrowDown") {
        event.preventDefault();
        if (menu.classList.contains("hidden")) {
          open();
          return;
        }
        activeIndex = Math.min(activeIndex + 1, visibleList.length - 1);
        highlight(visibleList);
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        activeIndex = Math.max(activeIndex - 1, 0);
        highlight(visibleList);
      } else if (event.key === "Enter") {
        if (!menu.classList.contains("hidden") && activeIndex >= 0 && visibleList[activeIndex]) {
          event.preventDefault();
          choose(visibleList[activeIndex]);
        }
      } else if (event.key === "Escape") {
        close();
      }
    });

    input.addEventListener("blur", function () {
      window.setTimeout(function () {
        if (!root.contains(document.activeElement)) close();
      }, 120);
    });

    options.forEach(function (opt) {
      opt.addEventListener("mousedown", function (event) {
        event.preventDefault();
        choose(opt);
      });
    });

    document.addEventListener("click", function (event) {
      if (!root.contains(event.target)) close();
    });

    if (select.form) {
      select.form.addEventListener("submit", function () {
        if (select.value) return;
        const typed = input.value.trim().toLowerCase();
        const match = options.filter(matches).find(function (opt) {
          return opt.textContent.trim().toLowerCase() === typed;
        });
        if (match) select.value = match.getAttribute("data-value");
      });
    }
  }

  function initComboboxes() {
    document.querySelectorAll("[data-combobox]").forEach(initCombobox);
  }

  // ── Tukar akun asal/tujuan pada transfer ──
  function initSwapAccounts() {
    const button = document.querySelector("[data-swap-accounts]");
    if (!button) return;
    button.addEventListener("click", function () {
      const form = button.closest("form");
      if (!form) return;
      const from = form.querySelector("[name='account_id']");
      const to = form.querySelector("[name='account_to_id']");
      if (!from || !to) return;
      const swap = from.value;
      from.value = to.value;
      to.value = swap;
    });
  }

  function init() {
    document.querySelectorAll("[data-alert]").forEach(initAlert);
    document.querySelectorAll("input[data-money]").forEach(initMoneyInput);
    initSegmented();
    initTypeFields();
    initComboboxes();
    initSwapAccounts();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
