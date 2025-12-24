import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../auth";

export default function Layout({ children }: { children: React.ReactNode }) {
  const { token, me, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-slate-50">
      <header className="sticky top-0 z-10 border-b border-white/10 bg-black/30 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link to="/" className="text-lg font-semibold tracking-tight">
            Поиск источников
          </Link>
          <nav className="flex items-center gap-3 text-sm">
            <NavLink
              to="/"
              className={({ isActive }) =>
                `rounded-lg px-3 py-1.5 hover:bg-white/10 ${
                  isActive ? "bg-white/10" : ""
                }`
              }
            >
              🔎 Поиск
            </NavLink>
            {me?.role === "admin" ? (
              <NavLink
                to="/panel"
                className={({ isActive }) =>
                  `rounded-lg px-3 py-1.5 hover:bg-white/10 ${
                    isActive ? "bg-white/10" : ""
                  }`
                }
              >
                🛠️ Панель
              </NavLink>
            ) : null}
            {!token ? (
              <>
                <NavLink
                  to="/login"
                  className="rounded-lg px-3 py-1.5 hover:bg-white/10"
                >
                  🔐 Войти
                </NavLink>
                <NavLink
                  to="/register"
                  className="rounded-lg px-3 py-1.5 hover:bg-white/10"
                >
                  ✍️ Регистрация
                </NavLink>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <span className="hidden text-xs text-slate-300 sm:inline">
                  {me?.email || "Аккаунт"}
                </span>
                <button
                  onClick={logout}
                  className="rounded-lg px-3 py-1.5 hover:bg-white/10"
                >
                  🚪 Выйти
                </button>
              </div>
            )}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
    </div>
  );
}
