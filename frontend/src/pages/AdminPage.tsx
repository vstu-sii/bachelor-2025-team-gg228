import { useEffect, useMemo, useRef, useState } from "react";
import {
  createUser,
  deleteDocument,
  getMetrics,
  listDocuments,
  listUsers,
  updateUser,
  uploadDocumentWithProgress,
  UserOut,
} from "../api";
import { useAuth } from "../auth";
import { useNavigate } from "react-router-dom";

export default function AdminPage() {
  const { token, me } = useAuth();
  const nav = useNavigate();
  const [docs, setDocs] = useState<any[]>([]);
  const [users, setUsers] = useState<UserOut[]>([]);
  const [metrics, setMetrics] = useState<any | null>(null);
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"docs" | "users" | "metrics">("docs");
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const friendlyError = (raw: any) => {
    const msg = String(raw?.message || raw || "");
    try {
      const obj = JSON.parse(msg);
      if (obj && typeof obj === "object" && "detail" in obj) return String((obj as any).detail);
    } catch {
      // ignore
    }
    return msg || "Ошибка";
  };

  const isAdmin = useMemo(() => me?.role === "admin", [me?.role]);

  useEffect(() => {
    if (!token) {
      nav("/login");
      return;
    }
  }, [token]);

  useEffect(() => {
    if (!token) return;
    if (me && !isAdmin) nav("/");
  }, [token, me, isAdmin]);

  const reload = async () => {
    if (!token) return;
    try {
      const d = await listDocuments(token);
      setDocs(d);
    } catch {
      setError("Не удалось загрузить документы");
    }
  };

  const reloadUsers = async () => {
    if (!token) return;
    try {
      const u = await listUsers(token);
      setUsers(u);
    } catch {
      setError("Не удалось загрузить пользователей");
    }
  };

  const reloadMetrics = async () => {
    if (!token) return;
    try {
      const m = await getMetrics(token);
      setMetrics(m);
    } catch {
      setError("Не удалось загрузить метрики");
    }
  };

  useEffect(() => {
    if (!token || !isAdmin) return;
    if (tab === "docs") reload();
    if (tab === "users") reloadUsers();
    if (tab === "metrics") reloadMetrics();
  }, [token, isAdmin, tab]);

  const onUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !file || !title.trim()) return;
    setLoading(true);
    setError(null);
    setUploadProgress(0);
    try {
      await uploadDocumentWithProgress(token, title, file, (p) => setUploadProgress(p));
      setTitle("");
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      await reload();
    } catch (e: any) {
      setError(friendlyError(e));
    } finally {
      setLoading(false);
      setUploadProgress(null);
    }
  };

  const onDelete = async (id: string) => {
    if (!token) return;
    if (!confirm("Удалить источник?")) return;
    setLoading(true);
    setError(null);
    try {
      await deleteDocument(token, id);
      await reload();
    } catch (e: any) {
      setError(friendlyError(e));
    } finally {
      setLoading(false);
    }
  };

  const onCreateUser = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!token) return;
    const form = new FormData(e.currentTarget);
    const email = String(form.get("email") || "");
    const password = String(form.get("password") || "");
    const role = String(form.get("role") || "user");
    setLoading(true);
    setError(null);
    try {
      await createUser(token, email, password, role);
      e.currentTarget.reset();
      await reloadUsers();
    } catch (e: any) {
      setError(friendlyError(e));
    } finally {
      setLoading(false);
    }
  };

  const toggleActive = async (u: UserOut) => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      await updateUser(token, u.id, { is_active: !u.is_active });
      await reloadUsers();
    } catch (e: any) {
      setError(friendlyError(e));
    } finally {
      setLoading(false);
    }
  };

  const toggleRole = async (u: UserOut) => {
    if (!token) return;
    const next = u.role === "admin" ? "user" : "admin";
    setLoading(true);
    setError(null);
    try {
      await updateUser(token, u.id, { role: next });
      await reloadUsers();
    } catch (e: any) {
      setError(friendlyError(e));
    } finally {
      setLoading(false);
    }
  };

  if (token && me && !isAdmin) {
    return (
      <div className="rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur">
        <h1 className="text-xl font-semibold">Доступ запрещён</h1>
        <p className="mt-2 text-sm text-slate-300">
          У вас нет прав для панели управления.
        </p>
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      <section className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur">
        <h1 className="text-xl font-semibold">Панель управления</h1>
        <p className="mt-1 text-sm text-slate-300">
          Управление данными и системой.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            onClick={() => setTab("docs")}
            className={`rounded-xl px-4 py-2 text-sm hover:bg-white/10 ${
              tab === "docs" ? "bg-white/10" : "bg-black/20"
            }`}
          >
            📚 Источники
          </button>
          <button
            onClick={() => setTab("users")}
            className={`rounded-xl px-4 py-2 text-sm hover:bg-white/10 ${
              tab === "users" ? "bg-white/10" : "bg-black/20"
            }`}
          >
            👥 Пользователи
          </button>
          <button
            onClick={() => setTab("metrics")}
            className={`rounded-xl px-4 py-2 text-sm hover:bg-white/10 ${
              tab === "metrics" ? "bg-white/10" : "bg-black/20"
            }`}
          >
            📈 Метрики
          </button>
        </div>

        {error && <div className="mt-3 text-sm text-red-300">{error}</div>}
      </section>

      {tab === "docs" ? (
        <section className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur">
          <h2 className="text-lg font-semibold">Источники</h2>

          <form
            onSubmit={onUpload}
            className="mt-4 grid gap-3 md:grid-cols-[1fr_auto]"
          >
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Название источника"
              required
              className="rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-sm outline-none ring-indigo-500/40 focus:ring"
            />
            <div className="flex items-center gap-2">
              <input
                ref={fileInputRef}
                type="file"
                required
                accept=".pdf,.docx"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="text-sm"
              />
              <button
                disabled={loading}
                className="rounded-xl bg-indigo-500 px-4 py-2 text-sm font-medium hover:bg-indigo-400 disabled:opacity-60"
              >
                {loading ? "Загружаю..." : "Загрузить"}
              </button>
            </div>
          </form>
          {uploadProgress !== null ? (
            <div className="mt-3">
              <div className="flex items-center justify-between text-xs text-slate-300">
                <span>Загрузка файла</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-black/40">
                <div
                  className="h-full rounded-full bg-indigo-500 transition-[width]"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          ) : null}

          {!docs.length && (
            <p className="mt-4 text-sm text-slate-400">Пока пусто.</p>
          )}
          <div className="mt-3 grid gap-2">
            {docs.map((d) => (
              <div
                key={d.id}
                className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/30 px-4 py-3"
              >
                <div>
                  <div className="text-sm font-medium">{d.title}</div>
                  <div className="text-xs text-slate-400">
                    {new Date(d.uploaded_at).toLocaleString()}
                  </div>
                </div>
                <button
                  onClick={() => onDelete(d.id)}
                  className="rounded-lg px-3 py-1 text-xs text-red-200 hover:bg-white/10"
                >
                  Удалить
                </button>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {tab === "users" ? (
        <section className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur">
          <h2 className="text-lg font-semibold">Пользователи</h2>

          <form onSubmit={onCreateUser} className="mt-4 grid gap-3 md:grid-cols-4">
            <input
              name="email"
              type="email"
              required
              placeholder="email"
              className="rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-sm outline-none ring-indigo-500/40 focus:ring"
            />
            <input
              name="password"
              type="password"
              required
              placeholder="пароль"
              className="rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-sm outline-none ring-indigo-500/40 focus:ring"
            />
            <select
              name="role"
              className="rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-sm outline-none ring-indigo-500/40 focus:ring"
              defaultValue="user"
            >
              <option value="user">user</option>
              <option value="admin">admin</option>
            </select>
            <button
              disabled={loading}
              className="rounded-xl bg-indigo-500 px-4 py-2 text-sm font-medium hover:bg-indigo-400 disabled:opacity-60"
            >
              {loading ? "Создаю..." : "Создать"}
            </button>
          </form>

          {!users.length && (
            <p className="mt-4 text-sm text-slate-400">Пока пусто.</p>
          )}
          <div className="mt-4 grid gap-2">
            {users.map((u) => (
              <div
                key={u.id}
                className="flex flex-col gap-2 rounded-2xl border border-white/10 bg-black/30 px-4 py-3 md:flex-row md:items-center md:justify-between"
              >
                <div>
                  <div className="text-sm font-medium">{u.email}</div>
                  <div className="text-xs text-slate-400">
                    {u.role} • {u.is_active ? "active" : "inactive"}
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => toggleRole(u)}
                    className="rounded-lg px-3 py-1 text-xs hover:bg-white/10"
                  >
                    {u.role === "admin" ? "Сделать user" : "Сделать admin"}
                  </button>
                  <button
                    onClick={() => toggleActive(u)}
                    className="rounded-lg px-3 py-1 text-xs hover:bg-white/10"
                  >
                    {u.is_active ? "Отключить" : "Включить"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {tab === "metrics" ? (
        <section className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur">
          <h2 className="text-lg font-semibold">Метрики</h2>
          {!metrics ? (
            <p className="mt-3 text-sm text-slate-400">Загружаю…</p>
          ) : (
            <>
              <div className="mt-4 grid gap-3 md:grid-cols-5">
                <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
                  <div className="text-xs text-slate-400">Пользователи</div>
                  <div className="mt-1 text-lg font-semibold">{metrics.total_users}</div>
                </div>
                <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
                  <div className="text-xs text-slate-400">Активные</div>
                  <div className="mt-1 text-lg font-semibold">{metrics.active_users}</div>
                </div>
                <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
                  <div className="text-xs text-slate-400">Источники</div>
                  <div className="mt-1 text-lg font-semibold">{metrics.total_documents}</div>
                </div>
                <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
                  <div className="text-xs text-slate-400">Поисков всего</div>
                  <div className="mt-1 text-lg font-semibold">{metrics.total_searches}</div>
                </div>
                <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
                  <div className="text-xs text-slate-400">За 24 часа</div>
                  <div className="mt-1 text-lg font-semibold">{metrics.searches_24h}</div>
                </div>
              </div>

              <h3 className="mt-6 text-sm font-semibold text-slate-200">
                Последние запросы
              </h3>
              <div className="mt-3 grid gap-2">
                {metrics.last_events.map((e: any) => (
                  <div
                    key={e.id}
                    className="rounded-2xl border border-white/10 bg-black/30 px-4 py-3"
                  >
                    <div className="text-xs text-slate-400">
                      {new Date(e.created_at).toLocaleString()} • {e.duration_ms}ms •{" "}
                      {e.results_count} результатов • {e.has_file ? "file" : "text"}
                    </div>
                    <div className="mt-1 text-sm text-slate-100">
                      {e.query_preview || `len=${e.query_len}`}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </section>
      ) : null}
    </div>
  );
}
