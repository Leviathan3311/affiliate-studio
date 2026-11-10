"use client";

import { useCallback, useEffect, useState } from "react";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SIGNED = "gp.signed";
const WORKSPACE = "gp.workspace";

// The session itself is an httpOnly cookie set by the API (page scripts cannot read it); this only
// remembers that one exists, to pick the landing page or the app on load.
export const session = {
  signedIn: () => typeof window !== "undefined" && localStorage.getItem(SIGNED) === "1",
  workspace: () => (typeof window === "undefined" ? null : localStorage.getItem(WORKSPACE)),
  markSignedIn: () => localStorage.setItem(SIGNED, "1"),
  setWorkspace: (id: string) => localStorage.setItem(WORKSPACE, id),
  clear: () => {
    localStorage.removeItem(SIGNED);
    localStorage.removeItem(WORKSPACE);
    localStorage.removeItem("gp.token"); // bearer token kept by older versions
  },
};

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public fields: Record<string, string> = {},
  ) {
    super(message);
  }
}

type FastApiDetail = string | { loc: (string | number)[]; msg: string }[];

/** Server messages are shown as they are only when written for people (Vietnamese); anything else
 * (an English status line, a provider error) becomes a plain sentence for its status code. */
function plain(status: number, detail: string | undefined): string {
  if (detail && /[À-ỹđĐ]/.test(detail)) return detail;
  if (status === 401) return "Phiên đăng nhập đã hết, vui lòng đăng nhập lại.";
  if (status === 403) return "Bạn không có quyền làm việc này.";
  if (status === 404) return "Không tìm thấy, có thể đã bị xoá.";
  if (status === 413) return "Tệp quá lớn.";
  if (status === 429) return "Đang có quá nhiều yêu cầu, thử lại sau ít phút.";
  if (status >= 500) return "Hệ thống đang bận, thử lại sau ít phút.";
  return "Chưa thực hiện được, vui lòng thử lại.";
}

export async function api<T>(path: string, init: RequestInit & { json?: unknown } = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const ws = session.workspace();
  if (ws) headers.set("X-Workspace-Id", ws);
  if (init.json !== undefined) headers.set("Content-Type", "application/json");

  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/v1${path}`, {
      credentials: "include",
      ...init,
      headers,
      body: init.json !== undefined ? JSON.stringify(init.json) : init.body,
    });
  } catch {
    throw new ApiError(0, "Không kết nối được máy chủ. Kiểm tra mạng rồi thử lại.");
  }
  if (res.status === 401 && typeof window !== "undefined" && !path.startsWith("/auth/")) {
    session.clear();
    // Full reload on purpose: drops every cached screen state for the expired session.
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.href = "/login";
  }
  if (res.status === 402 && typeof window !== "undefined" && window.location.pathname !== "/app/billing") {
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.href = "/app/billing";
  }
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail: FastApiDetail | undefined = body?.detail;
    if (Array.isArray(detail)) {
      const fields = Object.fromEntries(
        detail.map((d) => [String(d.loc[d.loc.length - 1]), d.msg.replace(/^Value error, /, "")]),
      );
      throw new ApiError(res.status, "Vui lòng kiểm tra các trường được đánh dấu.", fields);
    }
    throw new ApiError(res.status, plain(res.status, detail));
  }
  return body as T;
}

/** Minimal fetch-on-mount hook with optional polling. */
export function useApi<T>(path: string | null, pollMs?: number) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchInto = useCallback(
    (isLive: () => boolean = () => true) =>
      path
        ? api<T>(path).then(
            (d) => {
              if (!isLive()) return;
              setData(d);
              setError(null);
            },
            (e: ApiError) => isLive() && setError(e),
          )
        : Promise.resolve(),
    [path],
  );

  useEffect(() => {
    let live = true;
    const isLive = () => live; // ignore responses for a path we have left
    fetchInto(isLive);
    const id = pollMs
      ? setInterval(() => document.visibilityState === "visible" && fetchInto(isLive), pollMs)
      : undefined;
    return () => {
      live = false;
      clearInterval(id);
    };
  }, [fetchInto, pollMs]);

  const reload = useCallback(() => fetchInto(), [fetchInto]);

  return { data, error, loading: path !== null && data === null && error === null, reload, setData };
}

/** Current time, refreshed on an interval (render must stay pure). */
export function useNow(ms = 30000) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), ms);
    return () => clearInterval(id);
  }, [ms]);
  return now;
}
