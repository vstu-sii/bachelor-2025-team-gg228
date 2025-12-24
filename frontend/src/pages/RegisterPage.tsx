import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { register } from "../api";
import { useAuth } from "../auth";

export default function RegisterPage() {
  const { setToken } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await register(email, password);
      setToken(data.access_token);
      nav("/");
    } catch (e: any) {
      setError("Не удалось зарегистрироваться (возможно email занят)");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-md rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur">
      <h1 className="text-2xl font-semibold">Регистрация</h1>
      <form onSubmit={onSubmit} className="mt-6 grid gap-3">
        <label className="grid gap-1 text-sm">
          Email
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded-xl border border-white/10 bg-black/40 px-3 py-2 outline-none ring-indigo-500/40 focus:ring"
          />
        </label>
        <label className="grid gap-1 text-sm">
          Пароль
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-xl border border-white/10 bg-black/40 px-3 py-2 outline-none ring-indigo-500/40 focus:ring"
          />
        </label>

        <button
          disabled={loading}
          className="mt-2 rounded-xl bg-indigo-500 px-4 py-2 text-sm font-medium hover:bg-indigo-400 disabled:opacity-60"
        >
          {loading ? "Создаю..." : "Создать аккаунт"}
        </button>
        {error && <div className="text-sm text-red-300">{error}</div>}
      </form>
    </div>
  );
}

