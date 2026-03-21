import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { CategoryCard } from "components/catalog/CategoryCard";
import { FilterBar } from "components/catalog/FilterBar";
import { ProductCard } from "components/catalog/ProductCard";
import { EmptyState } from "components/common/EmptyState";
import { SearchBar } from "components/common/SearchBar";
import { SectionTitle } from "components/common/SectionTitle";
import { CategorySkeleton } from "components/skeletons/CategorySkeleton";
import { ProductSkeleton } from "components/skeletons/ProductSkeleton";
import type { Category, Product } from "types/api";
import { api } from "utils/api";

export function CatalogPage() {
  const { slug } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [categories, setCategories] = useState<Category[]>([]);
  const [category, setCategory] = useState<Category | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  const query = searchParams.get("query") ?? "";
  const sort = searchParams.get("sort") ?? "default";
  const discountOnly = searchParams.get("discount_only") === "true";
  const inStock = searchParams.get("in_stock") === "true";

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      const params = new URLSearchParams();
      if (slug) params.set("category_slug", slug);
      if (query) params.set("q", query);
      if (sort !== "default") params.set("sort", sort);
      if (discountOnly) params.set("discount_only", "true");
      if (inStock) params.set("in_stock", "true");

      try {
        const [categoriesResponse, productsResponse, categoryResponse] = await Promise.all([
          api.getCategories(),
          api.getProducts(params),
          slug ? api.getCategory(slug) : Promise.resolve(null),
        ]);
        if (!active) return;
        setCategories(categoriesResponse);
        setProducts(productsResponse);
        setCategory(categoryResponse);
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [slug, query, sort, discountOnly, inStock]);

  const updateParam = (key: string, value: string | null) => {
    const next = new URLSearchParams(searchParams);
    if (!value) next.delete(key);
    else next.set(key, value);
    setSearchParams(next);
  };

  return (
    <div className="space-y-6">
      <section className="glass-card p-5">
        <SectionTitle
          eyebrow={slug ? "раздел" : "каталог"}
          title={category?.name ?? "Весь каталог"}
          subtitle={
            category?.description ??
            "Ищите по вкусу, фильтруйте по наличию и быстро открывайте нужные позиции из любой категории."
          }
        />
        <SearchBar initialValue={query} onSubmit={(value) => updateParam("query", value || null)} />
      </section>

      <FilterBar
        sort={sort}
        discountOnly={discountOnly}
        inStock={inStock}
        onSortChange={(value) => updateParam("sort", value === "default" ? null : value)}
        onDiscountToggle={() => updateParam("discount_only", discountOnly ? null : "true")}
        onStockToggle={() => updateParam("in_stock", inStock ? null : "true")}
      />

      {!slug ? (
        <section>
          <SectionTitle eyebrow="категории" title="Откройте раздел" subtitle="Каждая карточка ведёт в отдельную витрину внутри каталога." />
          <div className="grid grid-cols-1 gap-4">
            {loading
              ? Array.from({ length: 3 }).map((_, index) => <CategorySkeleton key={index} />)
              : categories.map((item) => <CategoryCard key={item.id} category={item} />)}
          </div>
        </section>
      ) : (
        <div className="flex flex-wrap gap-2">
          <Link to="/catalog" className="rounded-full bg-white/80 px-4 py-2 text-sm font-semibold text-tea-900 shadow-soft">
            Все категории
          </Link>
          {categories.map((item) => (
            <Link
              key={item.id}
              to={`/catalog/${item.slug}`}
              className={`rounded-full px-4 py-2 text-sm font-semibold shadow-soft ${
                slug === item.slug ? "bg-tea-900 text-white" : "bg-white/70 text-fog"
              }`}
            >
              {item.name}
            </Link>
          ))}
        </div>
      )}

      <section>
        <div className="mb-4 flex items-center justify-between">
          <SectionTitle eyebrow="товары" title="Подходящие позиции" subtitle="Карточки адаптированы под быстрый просмотр и добавление в корзину." />
          <div className="rounded-full bg-white/70 px-3 py-2 text-xs font-semibold text-fog shadow-soft">{products.length} товаров</div>
        </div>
        <div className="grid grid-cols-1 gap-4">
          {loading ? Array.from({ length: 4 }).map((_, index) => <ProductSkeleton key={index} />) : null}
          {!loading && products.length === 0 ? (
            <EmptyState
              title="Ничего не найдено"
              description="Попробуйте убрать часть фильтров или изменить поисковый запрос."
            />
          ) : null}
          {!loading ? products.map((product) => <ProductCard key={product.id} product={product} />) : null}
        </div>
      </section>
    </div>
  );
}

