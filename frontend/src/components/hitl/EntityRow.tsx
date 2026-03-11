import type { ApprovedEntity } from "@/types";
import { ENTITY_COLORS, type EntityType } from "@/types";
import { cn } from "@/lib/utils";

interface EntityRowProps {
  entity: ApprovedEntity;
}

function confidenceColor(confidence: number): string {
  if (confidence >= 0.8) return "text-accent-green";
  if (confidence >= 0.6) return "text-accent-amber";
  return "text-accent-red";
}

export function EntityRow({ entity }: EntityRowProps) {
  const colors = ENTITY_COLORS[entity.entity_type as EntityType] ?? "";

  return (
    <div className="flex items-center gap-2 rounded border border-border bg-screen px-3 py-2">
      <span
        className={cn(
          "inline-block rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase",
          colors,
        )}
      >
        {entity.entity_type}
      </span>
      <span className={cn("text-xs", confidenceColor(entity.confidence))}>
        {entity.confidence.toFixed(2)}
      </span>
      <p className="flex-1 truncate font-mono text-xs text-text-primary">
        {entity.original}
      </p>
    </div>
  );
}
