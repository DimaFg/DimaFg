"use client";

import { type ElementType, type ReactNode, useEffect, useRef, useState } from "react";

type Props = {
  as?: ElementType;
  className?: string;
  children: ReactNode;
} & Record<string, unknown>;

/** Плавное появление при прокрутке, как в прототипе. При prefers-reduced-motion CSS отключает анимацию. */
export function Reveal({ as: Tag = "div", className = "", children, ...rest }: Props) {
  const ref = useRef<HTMLElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setVisible(true);
          io.disconnect();
        }
      },
      { threshold: 0.15 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <Tag ref={ref} className={`${className} reveal${visible ? " in" : ""}`.trim()} {...rest}>
      {children}
    </Tag>
  );
}
