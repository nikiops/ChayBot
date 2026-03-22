import { Search } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

type SearchBarProps = {
  initialValue?: string;
  placeholder?: string;
  onSubmit: (value: string) => void;
};

export function SearchBar({ initialValue = "", placeholder = "Найти чай по названию или настроению", onSubmit }: SearchBarProps) {
  const [value, setValue] = useState(initialValue);

  useEffect(() => {
    setValue(initialValue);
  }, [initialValue]);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit(value.trim());
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-3 rounded-[1.5rem] border border-[#d4ad61]/18 bg-white/72 px-4 py-3 shadow-soft backdrop-blur-sm">
      <Search className="h-5 w-5 text-bark-700" />
      <input
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder={placeholder}
        className="w-full border-none bg-transparent text-sm text-tea-900 outline-none placeholder:text-fog"
      />
      <button
        type="submit"
        className="pressable rounded-full bg-tea-900 px-4 py-2 text-xs font-semibold text-white"
      >
        Найти
      </button>
    </form>
  );
}
