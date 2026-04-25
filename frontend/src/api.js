import { getInitData } from "./telegram.js";

const API_BASE = import.meta.env.VITE_API_URL || "";

export async function apiFetch(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const initData = getInitData();

  if (initData) {
    headers["X-Telegram-Init-Data"] = initData;
  } else {
    headers["X-Dev-User"] = "true";
  }

  let body = options.body;
  if (body && !(body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    body
  });

  if (!response.ok) {
    let message = "Ошибка запроса";
    try {
      const payload = await response.json();
      if (Array.isArray(payload.detail)) {
        message = payload.detail[0]?.msg || message;
      } else {
        message = payload.detail || message;
      }
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  if (response.status === 204) return null;
  return response.json();
}
