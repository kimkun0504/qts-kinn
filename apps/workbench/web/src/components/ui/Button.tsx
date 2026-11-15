import type { ButtonHTMLAttributes } from "react";

export function Button({ className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      className={`min-h-8 cursor-pointer rounded-md border border-line bg-surface px-3 text-[13px] font-medium text-ink hover:bg-raised focus-visible:outline-2 focus-visible:outline-accent ${className}`}
      {...props}
    />
  );
}
