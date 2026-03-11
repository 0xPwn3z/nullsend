import { useState, useCallback, useRef, useEffect } from "react";
import { SendButton } from "./SendButton";
import { useAnalyze } from "@/hooks/useAnalyze";
import { useHITLStore } from "@/store/hitl";

export function PromptInput() {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { analyze, isAnalyzing } = useAnalyze();
  const hitlStatus = useHITLStore((s) => s.status);

  const isDisabled = isAnalyzing || hitlStatus === "reviewing" || hitlStatus === "approved";

  const handleSubmit = useCallback(async () => {
    const trimmed = text.trim();
    if (!trimmed || isDisabled) return;
    try {
      await analyze(trimmed);
      setText("");
    } catch (err: unknown) {
      // Error will be handled by the conversation feed
    }
  }, [text, isDisabled, analyze]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit],
  );

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [text]);

  // Re-focus after HITL flow completes
  useEffect(() => {
    if (hitlStatus === "idle") {
      textareaRef.current?.focus();
    }
  }, [hitlStatus]);

  return (
    <div className="border-t border-border bg-surface p-3">
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isDisabled}
          placeholder={
            isDisabled
              ? "Review entities before sending..."
              : "Type your prompt... (Enter to send, Shift+Enter for newline)"
          }
          rows={1}
          className="flex-1 resize-none rounded border border-border bg-screen px-4 py-2.5 text-sm text-text-primary placeholder:text-text-dim focus:border-accent-cyan/50 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
        />
        <SendButton disabled={isDisabled || !text.trim()} onClick={handleSubmit} />
      </div>
    </div>
  );
}
