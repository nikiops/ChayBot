import type { PropsWithChildren } from "react";

import { BottomNav } from "components/layout/BottomNav";

export function AppShell({ children }: PropsWithChildren) {
  return (
    <div className="min-h-screen bg-paper-glow text-tea-900">
      <div className="mx-auto min-h-screen max-w-[460px] px-4 pb-12 pt-4 safe-bottom">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-bark-500/80">Golden Tea</p>
            <h1 className="font-display text-[2rem] font-semibold leading-none text-parchment">Чайная витрина</h1>
          </div>
          <div className="rounded-full border border-bark-500/30 bg-[#120f0c]/85 px-3 py-1 text-xs font-medium text-bark-500 shadow-soft">
            Mini App
          </div>
        </div>
        <main className="animate-float-in">{children}</main>
      </div>
      <BottomNav />
    </div>
  );
}
