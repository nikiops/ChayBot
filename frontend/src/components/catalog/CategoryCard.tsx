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
      className="pressable group relative block min-h-[184px] overflow-hidden rounded-4xl border border-white/10 shadow-card"
      style={{
        backgroundImage: `linear-gradient(180deg, rgba(10, 10, 9, 0.02) 0%, rgba(10, 10, 9, 0.84) 100%), url(${category.image_url})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      <div className="absolute inset-0 bg-gradient-to-t from-[#0c0b09]/92 via-[#0d0b09]/46 to-[#0c0b09]/12" />
      <div className="absolute inset-0 bg-gradient-to-br from-[#7b6728]/12 via-transparent to-transparent" />
      <div className="relative flex h-full flex-col justify-between p-4 text-white">
        <div className="flex justify-end">
          <span className="rounded-full border border-white/22 bg-black/18 p-2 text-white/90 backdrop-blur-md">
            <ArrowUpRight className="h-4 w-4" />
          </span>
        </div>
        <div className="rounded-[1.65rem] border border-white/10 bg-black/20 p-4 backdrop-blur-md">
          <div className="mb-3 flex items-start justify-between gap-3">
            <div>
              <h3 className="font-display text-[1.55rem] font-semibold leading-none text-[#fff4de]">{category.name}</h3>
              <p className="mt-2 max-w-[28ch] text-sm leading-5 text-white/78">{category.description}</p>
            </div>
          </div>
          <div className="flex items-center justify-between gap-3">
            <span className="rounded-full bg-white/14 px-3 py-1 text-xs font-semibold tracking-wide text-white/92">
              {category.product_count ?? 0} товаров
            </span>
            <span className="text-sm font-semibold text-[#f1debb]">Выбрать</span>
          </div>
        </div>
      </div>
    </Link>
  );
}
