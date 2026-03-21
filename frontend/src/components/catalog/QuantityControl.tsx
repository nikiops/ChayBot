type QuantityControlProps = {
  value: number;
  onDecrease: () => void;
  onIncrease: () => void;
};

export function QuantityControl({ value, onDecrease, onIncrease }: QuantityControlProps) {
  return (
    <div className="flex items-center gap-2 rounded-full bg-tea-100 px-2 py-2">
      <button type="button" onClick={onDecrease} className="pressable h-8 w-8 rounded-full bg-white text-lg font-bold">
        -
      </button>
      <span className="min-w-8 text-center text-sm font-bold text-tea-900">{value}</span>
      <button type="button" onClick={onIncrease} className="pressable h-8 w-8 rounded-full bg-white text-lg font-bold">
        +
      </button>
    </div>
  );
}

