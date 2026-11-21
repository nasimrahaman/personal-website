// The light switch.
//
// Every page is dark unless the reader has turned the switch at the top, and
// their own device remembers which. Nothing is sent anywhere.
//
// This file is loaded in the <head> without "defer", so that it runs before
// the page is drawn and a light page is never drawn dark first. The switch is
// in the page hidden; it is shown here, so it is never a control that does
// nothing. Pages without the switch (404) still take the reader's choice.

(function () {
  "use strict";

  var KEY = "theme";
  var root = document.documentElement;

  function wantsLight() {
    try {
      return localStorage.getItem(KEY) === "light";
    } catch (e) {
      return false; // Storage is closed to us: stay dark.
    }
  }

  function remember(light) {
    try {
      if (light) localStorage.setItem(KEY, "light");
      else localStorage.removeItem(KEY);
    } catch (e) {}
  }

  function show(light) {
    if (light) root.setAttribute("data-theme", "light");
    else root.removeAttribute("data-theme");

    // The colour a phone gives its own bars around the page.
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", light ? "#ffffff" : "#000000");

    var button = document.querySelector("button.theme");
    if (button) {
      button.setAttribute("aria-pressed", light ? "true" : "false");
      button.title = light ? "Dark" : "Light";
    }
  }

  show(wantsLight());

  document.addEventListener("DOMContentLoaded", function () {
    show(wantsLight());

    var button = document.querySelector("button.theme");
    if (!button) return;
    button.hidden = false;
    button.addEventListener("click", function () {
      var light = root.getAttribute("data-theme") !== "light";
      remember(light);
      show(light);
    });
  });

  // A page brought back by the Back button may have been drawn before the
  // switch was turned on another page.
  window.addEventListener("pageshow", function (event) {
    if (event.persisted) show(wantsLight());
  });
})();
