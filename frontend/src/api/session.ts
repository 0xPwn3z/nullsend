import { apiFetch } from "./client";
import type { NewSessionResponse } from "@/types";

export async function createSession(
  name: string,
): Promise<NewSessionResponse> {
  return apiFetch<NewSessionResponse>("/session/new", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export async function deleteSession(
  sessionId: string,
): Promise<{ expired_tokens: number }> {
  return apiFetch<{ expired_tokens: number }>(`/session/${sessionId}`, {
    method: "DELETE",
  });
}
