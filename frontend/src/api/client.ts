const BASE_URL = "/api";

export async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(
      (body as { detail?: string }).detail ?? `HTTP ${res.status}`,
    );
  }

  return res.json() as Promise<T>;
}

export function apiStreamUrl(path: string): string {
  return `${BASE_URL}${path}`;
}
