import { Link } from "react-router-dom";

import { EmptyState } from "components/common/EmptyState";

export function NotFoundPage() {
  return (
    <EmptyState
      title="Такой страницы нет"
      description="Вернитесь на главную витрину или откройте каталог."
      action={
        <Link to="/" className="pressable rounded-full bg-tea-900 px-5 py-3 text-sm font-semibold text-white">
          На главную
        </Link>
      }
    />
  );
}

