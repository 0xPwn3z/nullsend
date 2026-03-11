import { Search } from "lucide-react";

export function HITLEmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-8 text-center">
      <Search className="h-8 w-8 text-text-dim" />
      <p className="text-sm text-text-muted">No entities detected.</p>
      <p className="text-xs text-text-dim">
        Review the prompt or add entities manually.
      </p>
    </div>
  );
}
