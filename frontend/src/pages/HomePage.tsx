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
        setFeatured(featuredResponse.slice(0, 4));
        setDiscounted(discountedResponse.slice(0, 4));
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
    <div className="space-y-7">
      <section className="glass-card overflow-hidden p-5">
        <div className="mb-5 flex items-center justify-between">
          <div className="rounded-full bg-bark-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-bark-700">
            Добро пожаловать
          </div>
          <Sparkles className="h-5 w-5 text-bark-500" />
        </div>
        <h2 className="font-display text-[2.35rem] font-semibold leading-[0.92] text-tea-900">
          {getTelegramUserName()},
          <br />
          выберите чай под настроение
        </h2>
        <p className="mt-4 max-w-[36ch] text-sm leading-6 text-fog">
          Премиальная витрина китайского чая с мягкими подборками, сезонными скидками и красивыми наборами для
          подарка.
        </p>
        <div className="mt-5">
          <SearchBar onSubmit={(value) => navigate(value ? `/catalog?query=${encodeURIComponent(value)}` : "/catalog")} />
        </div>
        <div className="mt-5 grid grid-cols-2 gap-3">
          <Link to="/catalog?discount_only=true" className="pressable rounded-[1.6rem] bg-tea-900 px-4 py-4 text-white">
            <p className="text-xs uppercase tracking-[0.24em] text-white/70">скидки недели</p>
            <p className="mt-2 text-lg font-bold">Товары со скидкой</p>
          </Link>
          <Link
            to="/catalog/gift-sets"
            className="pressable rounded-[1.6rem] bg-gradient-to-br from-bark-100 to-white px-4 py-4 text-tea-900"
          >
            <p className="text-xs uppercase tracking-[0.24em] text-bark-700/70">подарки</p>
            <p className="mt-2 text-lg font-bold">Готовые наборы</p>
          </Link>
        </div>
      </section>

      <section>
        <SectionTitle
          eyebrow="категории"
          title="Коллекции чая"
          subtitle="От глубокого пуэра до светлого белого чая и аксессуаров для домашней церемонии."
        />
        <div className="grid grid-cols-1 gap-4">
          {loading
            ? Array.from({ length: 4 }).map((_, index) => <CategorySkeleton key={index} />)
            : categories.slice(0, 5).map((category) => <CategoryCard key={category.id} category={category} />)}
        </div>
      </section>

      <section>
        <div className="mb-4 flex items-end justify-between">
          <SectionTitle eyebrow="подборка" title="Популярное" subtitle="Чаи, с которых удобно начать знакомство." />
          <Link to="/catalog" className="text-sm font-semibold text-tea-700">
            Весь каталог
          </Link>
        </div>
        <div className="grid grid-cols-1 gap-4">
          {loading
            ? Array.from({ length: 3 }).map((_, index) => <ProductSkeleton key={index} />)
            : featured.map((product) => <ProductCard key={product.id} product={product} />)}
        </div>
      </section>

      <section className="glass-card overflow-hidden p-5">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-bark-700/60">акция</p>
            <h3 className="font-display text-[2rem] font-semibold text-tea-900">Весенние предложения</h3>
          </div>
          <ArrowRight className="h-5 w-5 text-bark-500" />
        </div>
        <p className="mb-5 text-sm leading-6 text-fog">
          Сезонные боксы, улуны и фруктовые купажи с мягкой скидкой. Хорошая точка входа, если хочется открыть магазин
          клиенту уже сейчас.
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

