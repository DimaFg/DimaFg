"use client";

import { type RefObject, useEffect } from "react";

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select, textarea, [tabindex]:not([tabindex="-1"])';

/** Удерживает Tab внутри контейнеров, пока active === true. */
export function useFocusTrap(containers: RefObject<HTMLElement | null>[], active: boolean) {
  useEffect(() => {
    if (!active) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key !== "Tab") return;
      const items = containers
        .flatMap(({ current }) => {
          if (!current) return [];
          return [
            ...(current.matches(FOCUSABLE) ? [current] : []),
            ...Array.from(current.querySelectorAll<HTMLElement>(FOCUSABLE)),
          ];
        })
        .filter((el) => el.offsetParent !== null || el === document.activeElement);
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];
      const current = document.activeElement as HTMLElement | null;
      const inside = current ? items.includes(current) : false;
      if (e.shiftKey && (current === first || !inside)) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && (current === last || !inside)) {
        e.preventDefault();
        first.focus();
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [containers, active]);
}

/** Блокирует прокрутку страницы под открытым меню. */
export function useScrollLock(active: boolean) {
  useEffect(() => {
    if (!active) return;
    const root = document.documentElement;
    root.classList.add("scroll-locked");
    return () => root.classList.remove("scroll-locked");
  }, [active]);
}
