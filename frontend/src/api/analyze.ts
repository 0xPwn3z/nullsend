import { apiFetch } from "./client";
import type { AnalyzeResponse } from "@/types";

export async function analyzeText(
  text: string,
  sessionId: string,
): Promise<AnalyzeResponse> {
  return apiFetch<AnalyzeResponse>("/analyze", {
    method: "POST",
    body: JSON.stringify({ text, session_id: sessionId }),
  });
}
