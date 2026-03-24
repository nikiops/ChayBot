declare global {
  interface Window {
    __GOLDEN_TEA_CONFIG__?: {
      API_URL?: string;
      DEMO_USER_ID?: string;
      TELEGRAM_BOT_USERNAME?: string;
    };
  }
}

export function getRuntimeConfig() {
  if (typeof window === "undefined") {
    return {};
  }
  return window.__GOLDEN_TEA_CONFIG__ ?? {};
}

export function getRuntimeApiUrl() {
  return (getRuntimeConfig().API_URL ?? import.meta.env.VITE_API_URL ?? "/api").replace(/\/$/, "");
}

export function getRuntimeDemoUserId() {
  return getRuntimeConfig().DEMO_USER_ID ?? import.meta.env.VITE_DEMO_USER_ID ?? "900000001";
}

export function getRuntimeTelegramBotUsername() {
  return getRuntimeConfig().TELEGRAM_BOT_USERNAME ?? import.meta.env.VITE_TELEGRAM_BOT_USERNAME ?? "PGTEA_bot";
}

export function resolveMediaUrl(path: string | null | undefined) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;

  const apiUrl = getRuntimeApiUrl();
  if (apiUrl.startsWith("/")) {
    return `${window.location.origin}${path}`;
  }

  const base = apiUrl.replace(/\/api$/, "");
  return `${base}${path}`;
}
