type FilterBarProps = {
  sort: string;
  discountOnly: boolean;
  inStock: boolean;
  onSortChange: (value: string) => void;
  onDiscountToggle: () => void;
  onStockToggle: () => void;
};

export function FilterBar({ sort, discountOnly, inStock, onSortChange, onDiscountToggle, onStockToggle }: FilterBarProps) {
  return (
    <div className="glass-card flex flex-col gap-3 p-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-bold text-tea-900">Фильтры</p>
        <select
          value={sort}
          onChange={(event) => onSortChange(event.target.value)}
          className="rounded-full border border-tea-200 bg-white px-4 py-2 text-sm outline-none"
        >
          <option value="default">По умолчанию</option>
          <option value="price_asc">Сначала дешевле</option>
          <option value="price_desc">Сначала дороже</option>
        </select>
      </div>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onDiscountToggle}
          className={`pressable rounded-full px-4 py-2 text-sm font-semibold ${
            discountOnly ? "bg-bark-500 text-white" : "bg-bark-100 text-bark-700"
          }`}
        >
          Только скидки
        </button>
        <button
          type="button"
          onClick={onStockToggle}
          className={`pressable rounded-full px-4 py-2 text-sm font-semibold ${
            inStock ? "bg-tea-900 text-white" : "bg-tea-100 text-tea-900"
          }`}
        >
          В наличии
        </button>
      </div>
    </div>
  );
}

