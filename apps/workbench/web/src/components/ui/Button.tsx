import type { ButtonHTMLAttributes } from "react";

const VARIANTS = {
  plain: "border-line bg-surface text-ink hover:bg-raised",
  primary: "border-accent bg-accent text-on-accent hover:opacity-90",
  danger: "border-neg bg-surface text-neg hover:bg-raised",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof VARIANTS;
}

export function Button({ className = "", variant = "plain", ...props }: ButtonProps) {
  return (
    <button
      type="button"
      className={`min-h-8 cursor-pointer rounded-md border px-3 text-sm font-medium focus-visible:outline-2 focus-visible:outline-accent disabled:cursor-default disabled:opacity-50 ${VARIANTS[variant]} ${className}`}
      {...props}
    />
  );
}
