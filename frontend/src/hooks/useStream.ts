import { useCallback, useRef, useState } from "react";
import { startSendStream } from "@/api/send";
import type { DoneEventData, SendRequestBody } from "@/types";

interface UseStreamOptions {
  onChunk: (chunk: string) => void;
  onDone: (data: DoneEventData) => void;
  onError: (message: string) => void;
}

export function useStream(options: UseStreamOptions) {
  const [isStreaming, setIsStreaming] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);

  const startStream = useCallback(
    (body: SendRequestBody) => {
      setIsStreaming(true);
      controllerRef.current = startSendStream(body, {
        onChunk: options.onChunk,
        onDone: (data) => {
          setIsStreaming(false);
          controllerRef.current = null;
          options.onDone(data);
        },
        onError: (msg) => {
          setIsStreaming(false);
          controllerRef.current = null;
          options.onError(msg);
        },
      });
    },
    [options],
  );

  const abort = useCallback(() => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setIsStreaming(false);
  }, []);

  return { startStream, isStreaming, abort };
}
