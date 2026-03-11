import { useCallback, useState } from "react";
import { analyzeText } from "@/api/analyze";
import { useHITLStore } from "@/store/hitl";
import { useSessionStore } from "@/store/session";

export function useAnalyze() {
  const sessionId = useSessionStore((s) => s.session_id);
  const openReview = useHITLStore((s) => s.openReview);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const analyze = useCallback(
    async (text: string) => {
      if (!sessionId) throw new Error("No active session");
      setIsAnalyzing(true);
      try {
        const data = await analyzeText(text, sessionId);
        openReview(data.original_text, data.entities);
      } finally {
        setIsAnalyzing(false);
      }
    },
    [sessionId, openReview],
  );

  return { analyze, isAnalyzing };
}
