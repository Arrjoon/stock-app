import type { ReactNode } from "react";

type Props = {
  kicker: string;
  title: string;
  description?: ReactNode;
};

export function PageHeader({ kicker, title, description }: Props) {
  return (
    <header className="grid max-w-xl gap-2">
      <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-accent">{kicker}</p>
      <h1 className="m-0 text-[clamp(28px,3.4vw,36px)] font-semibold tracking-tight">{title}</h1>
      {description ? <p className="m-0 text-[15px] leading-relaxed text-ink-80">{description}</p> : null}
    </header>
  );
}
