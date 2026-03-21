import { getRuntimeDemoUserId } from "utils/runtime-config";

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        ready: () => void;
        expand: () => void;
        initData: string;
        initDataUnsafe?: {
          user?: {
            id: number;
            first_name: string;
            last_name?: string;
            username?: string;
          };
          start_param?: string;
        };
        HapticFeedback?: {
          impactOccurred: (style: "light" | "medium" | "heavy") => void;
          notificationOccurred: (type: "error" | "success" | "warning") => void;
        };
        setHeaderColor?: (color: string) => void;
        setBackgroundColor?: (color: string) => void;
      };
    };
  }
}

const demoUserId = getRuntimeDemoUserId();

export function getTelegramWebApp() {
  return window.Telegram?.WebApp;
}

export function initTelegramWebApp() {
  const webApp = getTelegramWebApp();
  if (!webApp) return;

  webApp.ready();
  webApp.expand();
  webApp.setHeaderColor?.("#080706");
  webApp.setBackgroundColor?.("#080706");
}

export function getAuthHeaders(): HeadersInit {
  const webApp = getTelegramWebApp();
  const userId = webApp?.initDataUnsafe?.user?.id;
  const storedDemoUserId = localStorage.getItem("demo_user_id") ?? demoUserId;

  if (!localStorage.getItem("demo_user_id")) {
    localStorage.setItem("demo_user_id", storedDemoUserId);
  }

  if (webApp?.initData) {
    return {
      Authorization: `TMA ${webApp.initData}`,
      "X-Telegram-Init-Data": webApp.initData,
      ...(userId ? { "X-Telegram-User-Id": String(userId) } : {}),
      ...(!userId ? { "X-Demo-User-Id": storedDemoUserId } : {}),
    };
  }

  return {
    ...(userId ? { "X-Telegram-User-Id": String(userId) } : {}),
    "X-Demo-User-Id": storedDemoUserId,
  };
}

export function getTelegramUserName(): string {
  const user = getTelegramWebApp()?.initDataUnsafe?.user;
  if (!user) return "Гость чайной лавки";
  return user.first_name || user.username || "Гость чайной лавки";
}

export function getStartParam(): string | null {
  const webApp = getTelegramWebApp();
  const url = new URL(window.location.href);
  return (
    webApp?.initDataUnsafe?.start_param ||
    url.searchParams.get("tgWebAppStartParam") ||
    url.searchParams.get("start")
  );
}

export function triggerSuccessHaptic() {
  getTelegramWebApp()?.HapticFeedback?.notificationOccurred("success");
}

export function triggerLightHaptic() {
  getTelegramWebApp()?.HapticFeedback?.impactOccurred("light");
}
