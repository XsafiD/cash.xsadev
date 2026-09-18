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
    const categoryCombos = Array.from(form.querySelectorAll("[data-combobox-category]"));

    function apply() {
      const type = select.value;

      fields.forEach(function (el) {
        const types = (el.getAttribute("data-type-field") || "").split(/\s+/);
        el.toggleAttribute("hidden", types.indexOf(type) === -1);
      });

      // Bersihkan akun tujuan saat bukan transfer agar tidak ikut terkirim.
      if (type !== "transfer") {
        const accountTo = form.querySelector("[name='account_to_id']");
        if (accountTo) {
          accountTo.value = "";
          accountTo.dispatchEvent(new Event("change", { bubbles: true }));
        }
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

      categoryCombos.forEach(function (root) {
        root.setAttribute("data-kind-filter", type === "transfer" ? "" : type);
        root.dispatchEvent(new Event("combobox:reset"));
      });
    }

    select.addEventListener("change", apply);
    apply();
  }

  // ── Dropdown custom: combobox (searchable) atau klik-saja ──
  function initCombobox(root) {
    const select = root.querySelector("[data-combobox-native]");
    const control = root.querySelector("[data-combobox-control]");
    const input = root.querySelector("[data-combobox-input]");
    const trigger = root.querySelector("[data-combobox-trigger]");
    const labelEl = root.querySelector("[data-combobox-label]");
    const menu = root.querySelector("[data-combobox-menu]");
    const empty = root.querySelector("[data-combobox-empty]");
    const options = Array.from(root.querySelectorAll("[data-combobox-option]"));
    const display = input || trigger;
    if (!select || !control || !display || !menu) return;

    const searchable = !!input;
    const placeholder = labelEl ? labelEl.getAttribute("data-placeholder") || "" : "";

    select.classList.add("hidden");
    control.classList.remove("hidden");

    let activeIndex = -1;

    function selectedOption() {
      return (
        options.find(function (opt) {
          return opt.getAttribute("data-value") === select.value;
        }) || null
      );
    }

    function syncDisplay() {
      const opt = selectedOption();
      if (input) {
        input.value = opt ? opt.textContent.trim() : "";
      } else if (labelEl) {
        labelEl.textContent = opt ? opt.textContent.trim() : placeholder;
        labelEl.classList.toggle("text-muted", !opt);
      }
    }

    function matches(opt) {
      const kind = root.getAttribute("data-kind-filter") || "";
      if (kind && opt.getAttribute("data-kind") !== kind) return false;
      if (!searchable) return true;
      const query = input.value.trim().toLowerCase();
      return !query || opt.textContent.toLowerCase().indexOf(query) !== -1;
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
      display.setAttribute("aria-expanded", "true");
    }

    function close() {
      menu.classList.add("hidden");
      root.classList.remove("is-open");
      display.setAttribute("aria-expanded", "false");
    }

    function choose(opt) {
      options.forEach(function (o) {
        o.setAttribute("aria-selected", "false");
      });
      opt.setAttribute("aria-selected", "true");
      select.value = opt.getAttribute("data-value");
      syncDisplay();
      close();
      select.dispatchEvent(new Event("change", { bubbles: true }));
    }

    function reset() {
      select.value = "";
      syncDisplay();
      close();
    }

    if (searchable) {
      input.addEventListener("focus", open);
      input.addEventListener("input", open);
      input.addEventListener("blur", function () {
        window.setTimeout(function () {
          if (!root.contains(document.activeElement)) close();
        }, 120);
      });
    } else {
      trigger.addEventListener("click", function () {
        if (menu.classList.contains("hidden")) open();
        else close();
      });
    }

    display.addEventListener("keydown", function (event) {
      const visibleList = options.filter(function (opt) {
        return !opt.classList.contains("hidden");
      });

      if (
        !searchable &&
        menu.classList.contains("hidden") &&
        (event.key === "Enter" || event.key === " ")
      ) {
        event.preventDefault();
        open();
        return;
      }

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

    options.forEach(function (opt) {
      opt.addEventListener("mousedown", function (event) {
        event.preventDefault();
        choose(opt);
      });
    });

    document.addEventListener("click", function (event) {
      if (!root.contains(event.target)) close();
    });

    select.addEventListener("change", syncDisplay);
    root.addEventListener("combobox:reset", reset);

    if (searchable && select.form) {
      select.form.addEventListener("submit", function () {
        if (select.value) return;
        const typed = input.value.trim().toLowerCase();
        const match = options.filter(matches).find(function (opt) {
          return opt.textContent.trim().toLowerCase() === typed;
        });
        if (match) select.value = match.getAttribute("data-value");
      });
    }

    syncDisplay();
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
      from.dispatchEvent(new Event("change", { bubbles: true }));
      to.dispatchEvent(new Event("change", { bubbles: true }));
    });
  }

  // ── Sidebar kiri: drawer pada layar kecil, statis pada layar besar ──
  function initSidebar() {
    const sidebar = document.querySelector("[data-sidebar]");
    const toggle = document.querySelector("[data-sidebar-toggle]");
    const backdrop = document.querySelector("[data-sidebar-backdrop]");
    if (!sidebar || !toggle || !backdrop) return;

    function open() {
      sidebar.classList.remove("-translate-x-full");
      backdrop.classList.remove("hidden");
      toggle.setAttribute("aria-expanded", "true");
    }

    function close() {
      sidebar.classList.add("-translate-x-full");
      backdrop.classList.add("hidden");
      toggle.setAttribute("aria-expanded", "false");
    }

    toggle.addEventListener("click", function () {
      if (sidebar.classList.contains("-translate-x-full")) open();
      else close();
    });

    backdrop.addEventListener("click", close);

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") close();
    });
  }

  function init() {
    document.querySelectorAll("[data-alert]").forEach(initAlert);
    initSidebar();
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
