"use client";

type Props = {
  label?: string;
};

export function LoadingState({ label = "Working…" }: Props) {
  return (
    <div className="flex items-center gap-2 text-sm text-ink-60" role="status">
      <span className="size-3.5 animate-spin rounded-full border-2 border-line border-t-accent" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
