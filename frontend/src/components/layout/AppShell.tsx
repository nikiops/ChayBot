import type { PropsWithChildren } from "react";

import { BottomNav } from "components/layout/BottomNav";
import { buildTelegramMiniAppUrl, isTelegramMiniApp } from "utils/telegram";

export function AppShell({ children }: PropsWithChildren) {
  const inTelegram = isTelegramMiniApp();

  return (
    <div className="min-h-screen bg-paper-glow text-tea-900">
      <div className="mx-auto min-h-screen max-w-[460px] px-4 pb-12 pt-4 safe-bottom">
        <div className="mb-5 flex items-start justify-between gap-3">
          <div className="max-w-[17rem]">
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-bark-500/80">Golden Tea</p>
            <h1 className="font-display text-[2rem] font-semibold leading-none text-parchment">Чайная витрина</h1>
            <p className="mt-1 text-xs leading-5 text-[#ead9b6]/82">Китайский чай для спокойной домашней церемонии.</p>
          </div>
          <div className="rounded-full border border-bark-500/24 bg-[#120f0c]/78 px-3 py-1.5 text-xs font-medium text-bark-500 shadow-soft">
            Mini App
          </div>
        </div>
        {!inTelegram ? (
          <div className="mb-5 rounded-[1.6rem] border border-[#d7b16a]/22 bg-white/10 px-4 py-4 shadow-soft backdrop-blur-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#d9c49c]/78">режим браузера</p>
            <p className="mt-2 text-sm leading-6 text-[#ead9b6]/88">
              Каталог доступен прямо здесь, а оформление заказа, корзина и избранное работают внутри Telegram Mini App.
            </p>
            <a
              href={buildTelegramMiniAppUrl()}
              target="_blank"
              rel="noreferrer"
              className="pressable mt-4 inline-flex rounded-full bg-tea-900 px-4 py-3 text-sm font-semibold text-white"
            >
              Перейти в Telegram
            </a>
          </div>
        ) : null}
        <main className="animate-float-in">{children}</main>
      </div>
      <BottomNav />
    </div>
  );
}
