import { useState } from "react";
import { searchSources, SearchResultItem } from "../api";
import { useAuth } from "../auth";

export default function SearchPage() {
  const { token } = useAuth();
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [minPercent, setMinPercent] = useState(30);
  const [rerank, setRerank] = useState(true);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async () => {
    const hasInput = Boolean(text.trim() || file);
    if (!hasInput) {
      setError("Введите текст или выберите файл");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const data = await searchSources(
        text.trim() || undefined,
        file || undefined,
        token,
        minPercent,
        rerank
      );
      setResults(data.results);
    } catch (e: any) {
      setError(e.message || "Ошибка поиска");
    } finally {
      setLoading(false);
    }
  };

  const onClear = () => {
    setText("");
    setFile(null);
    setResults([]);
    setError(null);
  };

  const canSubmit = Boolean(text.trim() || file) && !loading;

  return (
    <div className="grid gap-6">
      <section className="rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur">
        <h1 className="text-3xl font-semibold tracking-tight">
          Найдите источники по тексту
        </h1>
        <p className="mt-2 text-sm text-slate-300">
          Вставьте текст или загрузите PDF/DOCX. Мы покажем наиболее похожие
          источники из базы.
        </p>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="grid gap-2">
            <label className="text-sm text-slate-200">Текст запроса</label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={8}
              placeholder="Вставьте текст или оставьте пустым, если загружаете файл"
              className="w-full rounded-xl border border-white/10 bg-black/40 p-3 text-sm outline-none ring-indigo-500/40 focus:ring"
            />
          </div>

          <div className="grid gap-2">
            <label className="text-sm text-slate-200">Файл (PDF/DOCX)</label>
            <div className="flex flex-col items-start gap-3 rounded-xl border border-dashed border-white/20 bg-black/30 p-4">
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="text-sm"
              />
              {file && (
                <div className="text-xs text-slate-300">
                  Выбран: <span className="font-medium">{file.name}</span>
                </div>
              )}
              <p className="text-xs text-slate-400">
                Если выбран файл — текст сверху можно не заполнять.
              </p>
            </div>
          </div>
        </div>

        <div className="mt-5 grid gap-2">
          <div className="flex items-center justify-between text-sm text-slate-200">
            <span>Порог совпадения</span>
            <span className="text-slate-300">{minPercent}%</span>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="range"
              min={0}
              max={100}
              step={1}
              value={minPercent}
              onChange={(e) => setMinPercent(Number(e.target.value))}
              className="w-full accent-indigo-500"
            />
            <input
              type="number"
              min={0}
              max={100}
              value={minPercent}
              onChange={(e) => setMinPercent(Math.max(0, Math.min(100, Number(e.target.value))))}
              className="w-20 rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-sm outline-none ring-indigo-500/40 focus:ring"
            />
          </div>
          <p className="text-xs text-slate-400">
            Показываем результаты с похожестью ≥ выбранного процента.
          </p>
        </div>

        <div className="mt-4 flex items-center justify-between rounded-xl border border-white/10 bg-black/30 px-4 py-3">
          <div>
            <div className="text-sm text-slate-200">Улучшенный поиск</div>
            <div className="text-xs text-slate-400">
              Переранжирование источников моделью
            </div>
          </div>
          <button
            type="button"
            onClick={() => setRerank((v) => !v)}
            className={`h-7 w-12 rounded-full border border-white/10 p-1 transition ${
              rerank ? "bg-indigo-500/80" : "bg-black/40"
            }`}
            aria-pressed={rerank}
            aria-label="Улучшенный поиск"
          >
            <div
              className={`h-5 w-5 rounded-full bg-white transition ${
                rerank ? "translate-x-5" : "translate-x-0"
              }`}
            />
          </button>
        </div>

        <div className="mt-5 flex items-center gap-3">
          <button
            onClick={onSubmit}
            disabled={!canSubmit}
            className="rounded-xl bg-indigo-500 px-5 py-2 text-sm font-medium text-white shadow-lg shadow-indigo-500/30 hover:bg-indigo-400 disabled:opacity-60"
          >
            {loading ? "Ищу..." : "Найти источники"}
          </button>
          <button
            type="button"
            onClick={onClear}
            className="rounded-xl border border-white/10 bg-black/30 px-5 py-2 text-sm text-slate-200 hover:bg-white/10"
          >
            Очистить
          </button>
          {error && (
            <span className="text-sm text-red-300" role="alert" aria-live="polite">
              {error}
            </span>
          )}
        </div>
      </section>

      <section className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur">
        <h2 className="text-lg font-semibold">
          Результаты{results.length ? ` (${results.length})` : ""}
        </h2>
        {!results.length && (
          <p className="mt-2 text-sm text-slate-400">
            Тут появятся найденные источники.
          </p>
        )}
        <div className="mt-4 grid gap-3">
          {results.map((r, idx) => (
            <div
              key={`${r.document_id}-${r.page_number ?? "na"}-${idx}`}
              className="rounded-2xl border border-white/10 bg-black/30 p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-medium">{r.title}</div>
                  <div className="mt-1 text-xs text-slate-400">
                    совпадение: {Math.max(0, Math.min(100, r.score * 100)).toFixed(1)}%
                    {r.page_number ? ` • стр. ${r.page_number}` : ""}
                  </div>
                </div>
              </div>
              <p className="mt-3 text-sm text-slate-200">{r.excerpt}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
