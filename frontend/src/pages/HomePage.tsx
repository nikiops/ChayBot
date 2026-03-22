import { ArrowRight, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { CategoryCard } from "components/catalog/CategoryCard";
import { ProductCard } from "components/catalog/ProductCard";
import { EmptyState } from "components/common/EmptyState";
import { SearchBar } from "components/common/SearchBar";
import { SectionTitle } from "components/common/SectionTitle";
import { CategorySkeleton } from "components/skeletons/CategorySkeleton";
import { ProductSkeleton } from "components/skeletons/ProductSkeleton";
import type { Category, Product } from "types/api";
import { api } from "utils/api";
import { getTelegramUserName } from "utils/telegram";

export function HomePage() {
  const navigate = useNavigate();
  const [categories, setCategories] = useState<Category[]>([]);
  const [featured, setFeatured] = useState<Product[]>([]);
  const [discounted, setDiscounted] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const collectionCountLabel = loading ? "—" : String(categories.length);
  const featuredCountLabel = loading ? "—" : String(featured.length);
  const discountedCountLabel = loading ? "—" : String(discounted.length);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      try {
        const [categoriesResponse, featuredResponse, discountedResponse] = await Promise.all([
          api.getCategories(),
          api.getFeaturedProducts(),
          api.getProducts(new URLSearchParams({ discount_only: "true" })),
        ]);
        if (!active) return;
        setCategories(categoriesResponse);
        setFeatured(featuredResponse.slice(0, 3));
        setDiscounted(discountedResponse.slice(0, 2));
        setError(null);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Не удалось загрузить витрину.");
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  if (error) {
    return (
      <EmptyState
        title="Витрина пока не открылась"
        description="Проверьте, что backend доступен и seed-данные загружены."
        action={
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="pressable rounded-full bg-tea-900 px-5 py-3 text-sm font-semibold text-white"
          >
            Обновить
          </button>
        }
      />
    );
  }

  return (
    <div className="space-y-8">
      <section className="glass-card overflow-hidden p-5">
        <div className="mb-5 flex items-center justify-between gap-3">
          <div className="rounded-full border border-bark-500/18 bg-white/30 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-bark-700">
            Домашняя церемония
          </div>
          <Sparkles className="h-5 w-5 text-bark-500" />
        </div>
        <h2 className="font-display text-[2.2rem] font-semibold leading-[0.94] text-tea-900">
          {getTelegramUserName()},
          <br />
          витрина чая без суеты
        </h2>
        <p className="mt-4 max-w-[36ch] text-sm leading-6 text-fog">
          Спокойная подача китайского чая: откройте коллекции, найдите вкус по настроению и оформите заказ прямо
          внутри Telegram.
        </p>
        <div className="mt-5 flex flex-wrap gap-2">
          <span className="rounded-full bg-bark-100/75 px-3 py-1 text-xs font-semibold text-bark-700">Пуэры и улуны</span>
          <span className="rounded-full bg-bark-100/75 px-3 py-1 text-xs font-semibold text-bark-700">Подарочная подача</span>
          <span className="rounded-full bg-bark-100/75 px-3 py-1 text-xs font-semibold text-bark-700">Для домашнего ритуала</span>
        </div>
        <div className="mt-5">
          <SearchBar onSubmit={(value) => navigate(value ? `/catalog?query=${encodeURIComponent(value)}` : "/catalog")} />
        </div>
        <div className="mt-5 grid grid-cols-2 gap-3">
          <Link to="/catalog" className="pressable rounded-[1.5rem] bg-tea-900 px-4 py-4 text-white shadow-soft">
            <p className="text-xs uppercase tracking-[0.24em] text-white/70">каталог</p>
            <p className="mt-2 text-lg font-bold">Открыть все коллекции</p>
          </Link>
          <Link
            to="/catalog?discount_only=true"
            className="pressable rounded-[1.5rem] border border-bark-500/18 bg-white/36 px-4 py-4 text-tea-900 shadow-soft"
          >
            <p className="text-xs uppercase tracking-[0.24em] text-bark-700/70">предложения</p>
            <p className="mt-2 text-lg font-bold">Смотреть текущие скидки</p>
          </Link>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-3">
        <div className="rounded-[1.9rem] border border-white/10 bg-white/[0.045] p-5 shadow-soft backdrop-blur-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.26em] text-[#ccb486]/70">атмосфера</p>
          <div className="mt-3 flex items-start justify-between gap-4">
            <div>
              <h3 className="font-display text-[1.75rem] font-semibold leading-[0.96] text-parchment">
                Чай для тихого вечера, подарка или домашней паузы.
              </h3>
              <p className="mt-3 max-w-[34ch] text-sm leading-6 text-[#dbc8a8]/72">
                Главная витрина собрана компактно: сначала выбор коллекции, потом самые понятные позиции и аккуратные
                сезонные акценты.
              </p>
            </div>
            <ArrowRight className="mt-1 h-5 w-5 shrink-0 text-[#ccb486]/65" />
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-[1.55rem] border border-white/10 bg-white/[0.045] p-4 shadow-soft backdrop-blur-sm">
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[#ccb486]/70">коллекций</p>
            <p className="mt-2 text-2xl font-extrabold text-parchment">{collectionCountLabel}</p>
          </div>
          <div className="rounded-[1.55rem] border border-white/10 bg-white/[0.045] p-4 shadow-soft backdrop-blur-sm">
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[#ccb486]/70">в подборке</p>
            <p className="mt-2 text-2xl font-extrabold text-parchment">{featuredCountLabel}</p>
          </div>
          <div className="rounded-[1.55rem] border border-white/10 bg-white/[0.045] p-4 shadow-soft backdrop-blur-sm">
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[#ccb486]/70">со скидкой</p>
            <p className="mt-2 text-2xl font-extrabold text-parchment">{discountedCountLabel}</p>
          </div>
        </div>
      </section>

      <section>
        <div className="mb-4 flex items-end justify-between gap-4 rounded-[1.7rem] border border-white/10 bg-white/[0.055] px-4 py-4 shadow-soft backdrop-blur-sm">
          <SectionTitle
            eyebrow="категории"
            title="Коллекции чая"
            subtitle="От глубокого пуэра до светлых позиций и аксессуаров для красивой подачи."
          />
          <Link to="/catalog" className="shrink-0 text-sm font-semibold text-[#f0dfb7]">
            Все разделы
          </Link>
        </div>
        <div className="grid grid-cols-1 gap-4">
          {loading
            ? Array.from({ length: 4 }).map((_, index) => <CategorySkeleton key={index} />)
            : categories.slice(0, 4).map((category) => <CategoryCard key={category.id} category={category} />)}
        </div>
      </section>

      <section>
        <div className="mb-4 flex items-end justify-between gap-4 rounded-[1.7rem] border border-white/10 bg-white/[0.055] px-4 py-4 shadow-soft backdrop-blur-sm">
          <SectionTitle eyebrow="подборка" title="Популярное" subtitle="Чаи, с которых удобно начать знакомство." />
          <Link to="/catalog" className="shrink-0 text-sm font-semibold text-[#f0dfb7]">
            Весь каталог
          </Link>
        </div>
        <div className="grid grid-cols-1 gap-4">
          {loading
            ? Array.from({ length: 3 }).map((_, index) => <ProductSkeleton key={index} />)
            : featured.map((product) => <ProductCard key={product.id} product={product} />)}
        </div>
      </section>

      <section className="rounded-[1.9rem] border border-white/10 bg-white/[0.045] p-5 shadow-soft backdrop-blur-sm">
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[#ccb486]/70">акция</p>
            <h3 className="font-display text-[1.9rem] font-semibold text-parchment">Сезонные предложения</h3>
          </div>
          <ArrowRight className="h-5 w-5 shrink-0 text-[#ccb486]/65" />
        </div>
        <p className="mb-5 max-w-[38ch] text-sm leading-6 text-[#dbc8a8]/74">
          Небольшая выборка позиций со скидкой для быстрого входа в ассортимент. Без перегрузки, но с акцентом на
          выгодные позиции.
        </p>
        <div className="grid grid-cols-1 gap-4">
          {loading
            ? Array.from({ length: 2 }).map((_, index) => <ProductSkeleton key={index} />)
            : discounted.map((product) => <ProductCard key={product.id} product={product} />)}
        </div>
      </section>
    </div>
  );
}
