/** Centralized API helpers with error parsing. */

const API_BASE = import.meta.env.VITE_API_URL ?? "";

function parseErrorDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((e) => e.msg ?? JSON.stringify(e)).join("; ");
  }
  return JSON.stringify(detail);
}

export async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const msg = parseErrorDetail(err.detail) || JSON.stringify(err);
    throw new Error(msg);
  }
  return res.json();
}

export async function apiUpload(chatId, files) {
  const form = new FormData();
  for (const f of files) form.append("files", f);
  const res = await fetch(`${API_BASE}/chats/${chatId}/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const msg = parseErrorDetail(err.detail) || "Upload failed";
    throw new Error(msg);
  }
  return res.json();
}
