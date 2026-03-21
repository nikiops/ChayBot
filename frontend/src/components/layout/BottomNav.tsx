import { Heart, Home, Info, LayoutGrid, ShoppingBag } from "lucide-react";
import { NavLink } from "react-router-dom";

import { useCartStore } from "store/cart-store";

const items = [
  { to: "/", label: "Главная", icon: Home },
  { to: "/catalog", label: "Каталог", icon: LayoutGrid },
  { to: "/cart", label: "Корзина", icon: ShoppingBag },
  { to: "/favorites", label: "Избранное", icon: Heart },
  { to: "/about", label: "О нас", icon: Info },
];

export function BottomNav() {
  const totalItems = useCartStore((state) => state.cart?.total_items ?? 0);

  return (
    <nav className="fixed bottom-3 left-1/2 z-20 w-[calc(100%-1rem)] max-w-[440px] -translate-x-1/2 rounded-[2rem] border border-bark-500/35 bg-[#24170d]/92 px-2 py-2 shadow-card backdrop-blur-2xl">
      <div className="grid grid-cols-5 gap-1">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `pressable relative flex min-h-[60px] flex-col items-center justify-center rounded-[1.4rem] text-[11px] font-semibold transition ${
                isActive
                  ? "bg-gradient-to-b from-[#F0CF82] to-[#D9A640] text-[#140d08] shadow-soft"
                  : "text-[#F6E4BA] hover:bg-white/6 hover:text-white"
              }`
            }
          >
            <item.icon className="mb-1 h-4 w-4" />
            {item.label}
            {item.to === "/cart" && totalItems > 0 ? (
              <span className="absolute right-3 top-2 inline-flex min-h-5 min-w-5 items-center justify-center rounded-full bg-[#F0CF82] px-1 text-[10px] font-bold text-[#140d08]">
                {totalItems}
              </span>
            ) : null}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
