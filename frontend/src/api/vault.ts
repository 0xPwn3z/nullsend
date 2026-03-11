import { apiFetch } from "./client";
import type { VaultResponse } from "@/types";

export async function fetchVaultTokens(
  sessionId: string,
): Promise<VaultResponse> {
  return apiFetch<VaultResponse>(`/vault/${sessionId}`);
}
