import { ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";

import type { Category } from "types/api";

type CategoryCardProps = {
  category: Category;
};

export function CategoryCard({ category }: CategoryCardProps) {
  return (
    <Link
      to={`/catalog/${category.slug}`}
      className="pressable group relative block min-h-[170px] overflow-hidden rounded-4xl shadow-card"
      style={{
        backgroundImage: `linear-gradient(180deg, rgba(19, 26, 18, 0.1) 0%, rgba(19, 26, 18, 0.84) 100%), url(${category.image_url})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      <div className="absolute inset-0 bg-gradient-to-t from-tea-900/85 via-tea-900/20 to-transparent" />
      <div className="relative flex h-full flex-col justify-end p-5 text-white">
        <div className="mb-3 flex items-start justify-between gap-3">
          <div>
            <h3 className="font-display text-[1.75rem] font-semibold leading-none">{category.name}</h3>
            <p className="mt-2 text-sm leading-5 text-white/82">{category.description}</p>
          </div>
          <span className="rounded-full border border-white/40 bg-white/10 p-2 backdrop-blur-sm">
            <ArrowUpRight className="h-4 w-4" />
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="rounded-full bg-white/16 px-3 py-1 text-xs font-semibold tracking-wide text-white/95">
            {category.product_count ?? 0} товаров
          </span>
          <span className="text-sm font-semibold">Выбрать</span>
        </div>
      </div>
    </Link>
  );
}
