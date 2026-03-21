import { Link } from "react-router-dom";

export function AboutPage() {
  return (
    <div className="space-y-5">
      <section className="glass-card p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-tea-700/60">о нас</p>
        <h2 className="font-display text-[2.2rem] font-semibold leading-[0.94] text-tea-900">
          Магазин китайского чая
          <br />
          для красивых домашних ритуалов
        </h2>
        <p className="mt-4 text-sm leading-7 text-fog">
          Мы собираем спокойную, современную витрину с выразительными чаями, понятными подборками и атмосферной подачей.
          В центре внимания не сухой ассортимент, а опыт: вкус, история, текстура и ощущение качества.
        </p>
      </section>

      <section className="glass-card p-5">
        <h3 className="text-lg font-bold text-tea-900">Почему именно китайский чай</h3>
        <p className="mt-3 text-sm leading-7 text-fog">
          Китайский чай даёт редкое разнообразие: светлый и деликатный белый чай, живые зелёные сорта, многослойные
          улуны и глубокие пуэры. Это позволяет подбирать чай не только по цене, но и по настроению, времени дня и
          сценарию подачи.
        </p>
      </section>

      <section className="glass-card p-5">
        <h3 className="text-lg font-bold text-tea-900">Что мы делаем в MVP</h3>
        <ul className="mt-3 space-y-3 text-sm leading-6 text-fog">
          <li>Подбираем чай по вкусу и настроению.</li>
          <li>Показываем подарочные наборы и аксессуары.</li>
          <li>Оформляем заказ прямо внутри Telegram.</li>
          <li>Готовим архитектуру под будущие платежи, доставку и промокоды.</li>
        </ul>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link to="/contacts" className="pressable inline-flex rounded-full bg-tea-900 px-5 py-3 text-sm font-semibold text-white">
            Перейти к контактам
          </Link>
          <Link to="/admin" className="pressable inline-flex rounded-full bg-bark-100 px-5 py-3 text-sm font-semibold text-bark-700">
            Открыть admin
          </Link>
        </div>
      </section>
    </div>
  );
}
