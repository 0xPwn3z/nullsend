import { useState, useEffect, useCallback } from "react";
import { Eye, EyeOff } from "lucide-react";
import { ENTITY_COLORS, type EntityType } from "@/types";
import { cn } from "@/lib/utils";

interface TokenRowProps {
  tokenId: string;
  entityType: string;
  originalValue: string;
  createdAt: string;
}

export function TokenRow({
  tokenId,
  entityType,
  originalValue,
}: TokenRowProps) {
  const [revealed, setRevealed] = useState(false);
  const colors = ENTITY_COLORS[entityType as EntityType] ?? "";

  const reveal = useCallback(() => setRevealed(true), []);

  // Auto-hide after 5 seconds
  useEffect(() => {
    if (!revealed) return;
    const timer = setTimeout(() => setRevealed(false), 5000);
    return () => clearTimeout(timer);
  }, [revealed]);

  return (
    <div className="flex items-center justify-between gap-2 rounded border border-border bg-screen px-3 py-2">
      <div className="flex-1 overflow-hidden">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "inline-block rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase",
              colors,
            )}
          >
            {entityType}
          </span>
          <span className="font-mono text-[10px] text-text-dim">
            {tokenId}
          </span>
        </div>
        <p className="mt-1 truncate font-mono text-xs text-text-primary">
          {revealed ? originalValue : "••••••••"}
        </p>
      </div>
      <button
        onClick={revealed ? () => setRevealed(false) : reveal}
        className="rounded p-1 text-text-dim hover:bg-surface-raised hover:text-text-muted"
        title={revealed ? "Hide" : "Reveal (5s)"}
      >
        {revealed ? (
          <EyeOff className="h-3.5 w-3.5" />
        ) : (
          <Eye className="h-3.5 w-3.5" />
        )}
      </button>
    </div>
  );
}
