"use client";

type Props = {
  message: string;
  onRetry?: () => void;
};

export function ErrorState({ message, onRetry }: Props) {
  return (
    <div className="mt-3 flex items-center justify-between gap-3 rounded-[10px] bg-danger-bg px-3.5 py-3 text-danger" role="alert">
      <p className="m-0">{message}</p>
      {onRetry ? (
        <button
          type="button"
          className="inline-flex min-h-8 shrink-0 items-center rounded-[10px] border border-[rgba(240,164,164,0.4)] px-3 text-sm font-semibold"
          onClick={onRetry}
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}
