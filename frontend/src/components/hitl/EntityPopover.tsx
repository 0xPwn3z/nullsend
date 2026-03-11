import { useState, useRef, useEffect, useCallback } from "react";
import { Trash2 } from "lucide-react";
import { ALL_ENTITY_TYPES, type EntityType, type ApprovedEntity } from "@/types";

interface EntityPopoverProps {
  anchorRect: DOMRect | null;
  mode: "edit" | "add";
  entity?: ApprovedEntity;
  selectedText?: string;
  onSave: (patch: Partial<ApprovedEntity>) => void;
  onDelete?: () => void;
  onClose: () => void;
}

export function EntityPopover({
  anchorRect,
  mode,
  entity,
  selectedText,
  onSave,
  onDelete,
  onClose,
}: EntityPopoverProps) {
  const [entityType, setEntityType] = useState<EntityType>(
    entity?.entity_type ?? "IP_ADDRESS",
  );
  const [originalValue, setOriginalValue] = useState(
    entity?.original ?? selectedText ?? "",
  );

  const popoverRef = useRef<HTMLDivElement>(null);

  // Reset internal state when props change
  useEffect(() => {
    setEntityType(entity?.entity_type ?? "IP_ADDRESS");
    setOriginalValue(entity?.original ?? selectedText ?? "");
  }, [entity, selectedText]);

  // Close on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  // Close on click outside
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(e.target as Node)
      ) {
        onClose();
      }
    };
    // Use a timeout so the opening click doesn't immediately close
    const timer = setTimeout(() => {
      document.addEventListener("mousedown", handleClick);
    }, 0);
    return () => {
      clearTimeout(timer);
      document.removeEventListener("mousedown", handleClick);
    };
  }, [onClose]);

  const handleSave = useCallback(() => {
    if (mode === "edit") {
      onSave({ original: originalValue, entity_type: entityType });
    } else {
      onSave({
        original: originalValue,
        entity_type: entityType,
        confidence: 1.0,
      });
    }
  }, [mode, originalValue, entityType, onSave]);

  if (!anchorRect) return null;

  // Position: fixed, below anchor, clamped to viewport
  const top = anchorRect.bottom + 6;
  let left = anchorRect.left;
  const popoverWidth = 280;
  if (left + popoverWidth > window.innerWidth - 8) {
    left = window.innerWidth - popoverWidth - 8;
  }
  if (left < 8) left = 8;

  return (
    <div
      ref={popoverRef}
      style={{
        position: "fixed",
        top,
        left,
        zIndex: 50,
        background: "#0d1726",
        border: "1px solid #1e2d45",
        borderRadius: 6,
        boxShadow: "0 4px 24px rgba(0,0,0,0.5)",
        padding: 12,
        minWidth: 260,
      }}
    >
      {/* Row 1: type selector + confidence */}
      <div className="flex items-center gap-2 mb-2">
        <select
          value={entityType}
          onChange={(e) => setEntityType(e.target.value as EntityType)}
          className="flex-1 rounded border border-[#1e2d45] bg-[#0b1120] px-2 py-1 text-xs text-text-primary focus:border-[#00d4ff]/50 focus:outline-none"
        >
          {ALL_ENTITY_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        {mode === "edit" && entity && (
          <span className="text-[10px] text-text-dim whitespace-nowrap">
            conf: {entity.confidence.toFixed(2)}
          </span>
        )}
      </div>

      {/* Row 2: original value input */}
      {mode === "edit" && (
        <input
          type="text"
          value={originalValue}
          onChange={(e) => setOriginalValue(e.target.value)}
          className="w-full rounded border border-[#1e2d45] bg-[#0b1120] px-2 py-1.5 text-xs font-mono text-text-primary placeholder:text-text-dim focus:border-[#00d4ff]/50 focus:outline-none mb-3"
        />
      )}

      {/* Row 3: actions */}
      <div className="flex items-center justify-between gap-2">
        {mode === "edit" && onDelete && (
          <button
            onClick={onDelete}
            className="flex items-center gap-1 rounded px-2 py-1 text-xs text-red-400 hover:bg-red-400/10"
          >
            <Trash2 className="h-3 w-3" />
            Delete entity
          </button>
        )}

        {mode === "add" && <div />}

        <button
          onClick={handleSave}
          className="ml-auto rounded border border-[#00d4ff]/30 bg-[#00d4ff]/10 px-3 py-1 text-xs font-medium text-[#00d4ff] hover:bg-[#00d4ff]/20"
        >
          {mode === "edit" ? "Save" : "+ Add entity"}
        </button>
      </div>
    </div>
  );
}
