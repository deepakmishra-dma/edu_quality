import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Read Frappe's CSRF token injected by the Jinja template into window._csrf_token. */
export function getCsrfToken(): string {
  return (window as any)._csrf_token ?? "";
}
