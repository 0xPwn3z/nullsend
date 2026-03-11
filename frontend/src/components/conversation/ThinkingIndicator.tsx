import { Loader2 } from "lucide-react";

export function ThinkingIndicator() {
  return (
    <div className="flex w-full justify-start px-4 py-2">
      <div className="flex items-center gap-2 rounded border border-border bg-surface px-4 py-3 text-sm text-text-muted">
        <Loader2 className="h-4 w-4 animate-spin text-accent-cyan" />
        <span>Thinking...</span>
      </div>
    </div>
  );
}
