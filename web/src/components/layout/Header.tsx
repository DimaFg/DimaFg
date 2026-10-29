"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { site } from "@/config/site";
import { navigation } from "@/content/about";
import { useFocusTrap, useScrollLock } from "@/shared/lib/a11y";

const MOBILE_QUERY = "(max-width: 700px)";

export function Header() {
  const [open, setOpen] = useState(false);
  const navRef = useRef<HTMLElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const trapRefs = useMemo(() => [toggleRef, navRef], []);

  useFocusTrap(trapRefs, open);
  useScrollLock(open);

  const close = useCallback((restoreFocus: boolean) => {
    setOpen(false);
    if (restoreFocus) toggleRef.current?.focus();
  }, []);

  useEffect(() => {
    if (!open) return;
    navRef.current?.querySelector<HTMLElement>("a")?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close(true);
    };
    // При повороте экрана или расширении окна меню перестаёт быть «мобильным» — закрываем.
    const mq = window.matchMedia(MOBILE_QUERY);
    const onChange = () => !mq.matches && close(false);
    document.addEventListener("keydown", onKey);
    mq.addEventListener("change", onChange);
    return () => {
      document.removeEventListener("keydown", onKey);
      mq.removeEventListener("change", onChange);
    };
  }, [open, close]);

  return (
    <header className="site-header">
      <Link href="/" className="logo" aria-label={`${site.name} — на главную`}>
        Д<span>·</span>МИТРИЙ
      </Link>
      <button
        ref={toggleRef}
        type="button"
        className="nav-toggle"
        aria-expanded={open}
        aria-controls="site-nav"
        aria-label={open ? "Закрыть меню" : "Открыть меню"}
        onClick={() => setOpen((v) => !v)}
      >
        <span aria-hidden="true">{open ? "✕" : "☰"}</span>
      </button>
      {open && (
        <button
          type="button"
          className="nav-backdrop"
          aria-hidden="true"
          tabIndex={-1}
          onClick={() => close(true)}
        />
      )}
      <nav
        ref={navRef}
        id="site-nav"
        className={`site-nav${open ? " open" : ""}`}
        aria-label="Основная навигация"
      >
        {navigation.map((item) => (
          <Link key={item.href} href={item.href} onClick={() => close(false)}>
            {item.label}
          </Link>
        ))}
        <a
          className="tg"
          href={site.telegram.url}
          target="_blank"
          rel="noopener noreferrer"
          data-analytics="telegram_click"
          onClick={() => close(false)}
        >
          Telegram <span aria-hidden="true">→</span>
          <span className="visually-hidden"> (откроется в новой вкладке)</span>
        </a>
      </nav>
    </header>
  );
}
