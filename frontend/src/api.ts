const API_BASE = "/api";

export type SearchResultItem = {
  document_id: string;
  title: string;
  score: number;
  rerank_score?: number | null;
  excerpt: string;
  page_number?: number | null;
};

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      try {
        const data: any = await res.json();
        const msg =
          (data && typeof data === "object" && "detail" in data && String(data.detail)) ||
          JSON.stringify(data);
        throw new Error(msg || res.statusText);
      } catch (e: any) {
        throw new Error(e?.message || res.statusText);
      }
    }
    const txt = await res.text();
    throw new Error(txt?.trim() || res.statusText);
  }
  return res.json() as Promise<T>;
}

export async function login(email: string, password: string) {
  return apiFetch<{ access_token: string }>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export async function register(email: string, password: string) {
  return apiFetch<{ access_token: string }>("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export async function getMe(token: string) {
  return apiFetch<{ id: string; email: string; role: string; is_active: boolean }>(
    "/users/me",
    {},
    token
  );
}

export async function listDocuments(token: string) {
  return apiFetch<any[]>("/admin/documents", {}, token);
}

export async function uploadDocument(
  token: string,
  title: string,
  file: File
) {
  const fd = new FormData();
  fd.append("title", title);
  fd.append("file", file);
  return apiFetch<any>("/admin/documents", { method: "POST", body: fd }, token);
}

export function uploadDocumentWithProgress(
  token: string,
  title: string,
  file: File,
  onProgress: (percent: number) => void
) {
  return new Promise<any>((resolve, reject) => {
    const fd = new FormData();
    fd.append("title", title);
    fd.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/admin/documents", true);
    xhr.setRequestHeader("Authorization", `Bearer ${token}`);

    xhr.upload.onprogress = (evt) => {
      if (!evt.lengthComputable) return;
      const percent = Math.max(0, Math.min(100, Math.round((evt.loaded / evt.total) * 100)));
      onProgress(percent);
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch {
          resolve(xhr.responseText);
        }
      } else {
        reject(new Error(xhr.responseText || `HTTP ${xhr.status}`));
      }
    };

    xhr.onerror = () => reject(new Error("Network error"));
    xhr.onabort = () => reject(new Error("Upload aborted"));

    xhr.send(fd);
  });
}

export async function deleteDocument(token: string, id: string) {
  return apiFetch<{ ok: boolean }>(`/admin/documents/${id}`, { method: "DELETE" }, token);
}

export type UserOut = {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
};

export async function listUsers(token: string) {
  return apiFetch<UserOut[]>("/admin/users", {}, token);
}

export async function createUser(
  token: string,
  email: string,
  password: string,
  role: string
) {
  return apiFetch<UserOut>(
    "/admin/users",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, role }),
    },
    token
  );
}

export async function updateUser(
  token: string,
  id: string,
  data: { role?: string; is_active?: boolean; password?: string }
) {
  return apiFetch<UserOut>(
    `/admin/users/${id}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
    token
  );
}

export async function getMetrics(token: string) {
  return apiFetch<{
    total_users: number;
    active_users: number;
    total_documents: number;
    total_searches: number;
    searches_24h: number;
    last_events: Array<{
      id: string;
      created_at: string;
      user_id?: string | null;
      query_len: number;
      query_preview?: string | null;
      has_file: boolean;
      duration_ms: number;
      results_count: number;
    }>;
  }>("/admin/metrics", {}, token);
}

export async function searchSources(
  text?: string,
  file?: File,
  token?: string | null,
  minSimilarityPercent?: number,
  rerank: boolean = true
) {
  const fd = new FormData();
  if (text) fd.append("text", text);
  if (file) fd.append("file", file);
  if (typeof minSimilarityPercent === "number") {
    fd.append("min_similarity_percent", String(minSimilarityPercent));
  }
  fd.append("rerank", String(rerank));
  return apiFetch<{ query: string; results: SearchResultItem[] }>(
    "/search",
    {
      method: "POST",
      body: fd,
    },
    token || undefined
  );
}
