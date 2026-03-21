export function ContactsPage() {
  return (
    <div className="space-y-5">
      <section className="glass-card p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-tea-700/60">контакты</p>
        <h2 className="font-display text-[2.2rem] font-semibold text-tea-900">Связаться с чайной лавкой</h2>
      </section>
      <div className="glass-card space-y-4 p-5">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-tea-700/60">telegram</p>
          <a href="https://t.me/tea_boutique_manager" className="mt-2 block text-lg font-bold text-tea-900">
            @tea_boutique_manager
          </a>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-tea-700/60">телефон</p>
          <p className="mt-2 text-lg font-bold text-tea-900">+7 (900) 000-00-00</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-tea-700/60">адрес</p>
          <p className="mt-2 text-lg font-bold text-tea-900">Ташкент, ул. Чайная, 8</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-tea-700/60">часы работы</p>
          <p className="mt-2 text-lg font-bold text-tea-900">Ежедневно, 10:00-21:00</p>
        </div>
        <a href="https://t.me/tea_boutique_manager" className="pressable inline-flex rounded-full bg-tea-900 px-5 py-3 text-sm font-semibold text-white">
          Написать в Telegram
        </a>
      </div>
    </div>
  );
}

