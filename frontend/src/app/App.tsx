import { useEffect } from "react";
import { HashRouter, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";

import { AppShell } from "components/layout/AppShell";
import { AboutPage } from "pages/AboutPage";
import { AdminPage } from "pages/AdminPage";
import { CartPage } from "pages/CartPage";
import { CatalogPage } from "pages/CatalogPage";
import { CheckoutPage } from "pages/CheckoutPage";
import { ContactsPage } from "pages/ContactsPage";
import { FavoritesPage } from "pages/FavoritesPage";
import { HomePage } from "pages/HomePage";
import { OrderPage } from "pages/OrderPage";
import { ProductPage } from "pages/ProductPage";
import { useCartStore } from "store/cart-store";
import { useFavoritesStore } from "store/favorites-store";
import { getStartParam, initTelegramWebApp, isTelegramMiniApp } from "utils/telegram";

function Bootstrapper() {
  const fetchCart = useCartStore((state) => state.fetchCart);
  const fetchFavorites = useFavoritesStore((state) => state.fetchFavorites);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (!isTelegramMiniApp()) return;
    initTelegramWebApp();
    void fetchCart();
    void fetchFavorites();
  }, [fetchCart, fetchFavorites]);

  useEffect(() => {
    if (location.pathname !== "/") return;
    if (!isTelegramMiniApp()) return;
    const startParam = getStartParam();
    if (!startParam) return;

    if (startParam === "cart") {
      navigate("/cart", { replace: true });
      return;
    }
    if (startParam === "favorites") {
      navigate("/favorites", { replace: true });
      return;
    }
    if (startParam.startsWith("category:")) {
      navigate(`/catalog/${startParam.replace("category:", "")}`, { replace: true });
      return;
    }
    if (startParam.startsWith("product:")) {
      navigate(`/product/${startParam.replace("product:", "")}`, { replace: true });
      return;
    }
    if (startParam.startsWith("promo:")) {
      navigate("/catalog?discount_only=true", { replace: true });
    }
  }, [location.pathname, navigate]);

  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/catalog" element={<CatalogPage />} />
        <Route path="/catalog/:slug" element={<CatalogPage />} />
        <Route path="/product/:slug" element={<ProductPage />} />
        <Route path="/cart" element={<CartPage />} />
        <Route path="/checkout" element={<CheckoutPage />} />
        <Route path="/favorites" element={<FavoritesPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/contacts" element={<ContactsPage />} />
        <Route path="/order/:id" element={<OrderPage />} />
        <Route path="/home" element={<Navigate to="/" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}

export function App() {
  return (
    <HashRouter>
      <Bootstrapper />
    </HashRouter>
  );
}
