import { apiStreamUrl } from "./client";
import type { SendRequestBody, DoneEventData } from "@/types";

export interface StreamCallbacks {
  onChunk: (chunk: string) => void;
  onDone: (data: DoneEventData) => void;
  onError: (message: string) => void;
}

/**
 * Start an SSE stream for the /send endpoint.
 * Returns an AbortController so the caller can cancel.
 */
export function startSendStream(
  body: SendRequestBody,
  callbacks: StreamCallbacks,
): AbortController {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(apiStreamUrl("/send"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        callbacks.onError(`HTTP ${res.status}: ${res.statusText}`);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        // Keep the last (potentially incomplete) chunk in the buffer
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          const eventMatch = part.match(/^event:\s*(.+)$/m);
          const dataMatch = part.match(/^data:\s*(.+)$/m);

          if (!eventMatch || !dataMatch) continue;

          const eventType = eventMatch[1]!.trim();
          const rawData = dataMatch[1]!.trim();

          switch (eventType) {
            case "token": {
              const parsed = JSON.parse(rawData) as { chunk: string };
              callbacks.onChunk(parsed.chunk);
              break;
            }
            case "done": {
              const parsed = JSON.parse(rawData) as DoneEventData;
              callbacks.onDone(parsed);
              break;
            }
            case "error": {
              const parsed = JSON.parse(rawData) as { message: string };
              callbacks.onError(parsed.message);
              break;
            }
          }
        }
      }
    } catch (err: unknown) {
      if ((err as Error).name !== "AbortError") {
        callbacks.onError(
          err instanceof Error ? err.message : "Stream failed",
        );
      }
    }
  })();

  return controller;
}
