/*!
 * Color mode toggler for Bootstrap's docs (https://getbootstrap.com/)
 * Copyright 2011-2023 The Bootstrap Authors
 * Licensed under the Creative Commons Attribution 3.0 Unported License.
 */

(() => {
  "use strict";

  // Added type alias for supported themes
  type Theme = "light" | "dark" | "auto";

  // Typed localStorage helpers
  const getStoredTheme = (): Theme | null =>
    localStorage.getItem("theme") as Theme | null;
  const setStoredTheme = (theme: Theme): void =>
    localStorage.setItem("theme", theme);

  // Typed preferred theme resolver
  const getPreferredTheme = (): Theme => {
    const storedTheme = getStoredTheme();
    if (storedTheme) {
      return storedTheme;
    }

    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  };

  // Typed theme applier
  const setTheme = (theme: Theme): void => {
    if (
      theme === "auto" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    ) {
      document.documentElement.setAttribute("data-bs-theme", "dark");
    } else {
      document.documentElement.setAttribute("data-bs-theme", theme);
    }
  };

  setTheme(getPreferredTheme());

  // Typed UI updater
  const showActiveTheme = (theme: Theme, focus: boolean = false): void => {
    const themeSwitcher = document.querySelector<HTMLElement>("#bd-theme");

    if (!themeSwitcher) return;

    const themeSwitcherText = document.querySelector<HTMLElement>("#bd-theme-text");
    const activeThemeIcon = document.querySelector<SVGUseElement>(".theme-icon-active use");
    const btnToActive = document.querySelector<HTMLElement>(`[data-bs-theme-value="${theme}"]`);

    if (!activeThemeIcon || !btnToActive) return;

    const svgUse = btnToActive.querySelector<SVGUseElement>("svg use");
    const svgOfActiveBtn = svgUse?.getAttribute("href") || svgUse?.getAttribute("xlink:href") || "";

    document.querySelectorAll<HTMLElement>("[data-bs-theme-value]").forEach((element) => {
      element.classList.remove("active");
      element.setAttribute("aria-pressed", "false");
    });

    btnToActive.classList.add("active");
    btnToActive.setAttribute("aria-pressed", "true");
    if (svgOfActiveBtn) {
      activeThemeIcon.setAttribute("href", svgOfActiveBtn);
    }

    const baseText = themeSwitcherText?.textContent?.trim() || "Toggle theme";
    const chosenValue = (btnToActive.dataset.bsThemeValue as Theme) || theme;
    const themeSwitcherLabel = `${baseText} (${chosenValue})`;
    themeSwitcher.setAttribute("aria-label", themeSwitcherLabel);

    if (focus) {
      themeSwitcher.focus();
    }
  };

  window
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", () => {
      const storedTheme = getStoredTheme();
      if (storedTheme !== "light" && storedTheme !== "dark") {
        setTheme(getPreferredTheme());
      }
    });

  window.addEventListener("DOMContentLoaded", () => {
    showActiveTheme(getPreferredTheme());

    document.querySelectorAll<HTMLElement>("[data-bs-theme-value]").forEach((toggle) => {
      toggle.addEventListener("click", () => {
        const theme = (toggle.getAttribute("data-bs-theme-value") as Theme) || "light";
        setStoredTheme(theme);
        setTheme(theme);
        showActiveTheme(theme, true);
      });
    });
  });
})();
