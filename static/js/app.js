(function () {
  "use strict";

  var THOUSANDS = /\B(?=(\d{3})+(?!\d))/g;

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
      var existing = parseFloat(input.value);
      input.value = isNaN(existing) ? "" : formatRupiah(String(Math.round(existing)));
    }

    input.addEventListener("input", function () {
      var caretFromEnd = input.value.length - input.selectionStart;
      input.value = formatRupiah(input.value.replace(/\D/g, ""));
      var caret = Math.max(input.value.length - caretFromEnd, 0);
      input.setSelectionRange(caret, caret);
    });

    if (input.form) {
      input.form.addEventListener("submit", function () {
        input.value = input.value.replace(/\D/g, "");
      });
    }
  }

  function init() {
    document.querySelectorAll("[data-alert]").forEach(initAlert);
    document.querySelectorAll("input[data-money]").forEach(initMoneyInput);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
