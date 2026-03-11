import { useState } from "react";
import { Plus, X } from "lucide-react";
import { ALL_ENTITY_TYPES, type EntityType } from "@/types";
import { useHITLStore } from "@/store/hitl";

interface AddEntityFormProps {
  onClose: () => void;
}

export function AddEntityForm({ onClose }: AddEntityFormProps) {
  const [value, setValue] = useState("");
  const [entityType, setEntityType] = useState<EntityType>("IP_ADDRESS");
  const [error, setError] = useState("");
  const originalText = useHITLStore((s) => s.originalText);
  const addEntity = useHITLStore((s) => s.addEntity);

  const handleAdd = () => {
    const trimmed = value.trim();
    if (!trimmed) {
      setError("Enter a string to match.");
      return;
    }
    if (!originalText.includes(trimmed)) {
      setError("String not found in the original prompt.");
      return;
    }
    addEntity({ original: trimmed, entity_type: entityType, confidence: 1.0 });
    onClose();
  };

  return (
    <div className="rounded border border-accent-cyan/30 bg-surface-raised p-3">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs font-semibold text-text-primary">
          Add entity
        </span>
        <button
          onClick={onClose}
          className="rounded p-0.5 text-text-dim hover:text-text-muted"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="space-y-2">
        <input
          type="text"
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            setError("");
          }}
          placeholder="Enter string to anonymize..."
          className="w-full rounded border border-border bg-screen px-2 py-1.5 text-xs text-text-primary placeholder:text-text-dim focus:border-accent-cyan/50 focus:outline-none"
        />

        <select
          value={entityType}
          onChange={(e) => setEntityType(e.target.value as EntityType)}
          className="w-full rounded border border-border bg-screen px-2 py-1.5 text-xs text-text-primary focus:border-accent-cyan/50 focus:outline-none"
        >
          {ALL_ENTITY_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>

        {error && <p className="text-xs text-accent-red">{error}</p>}

        <div className="flex gap-2">
          <button
            onClick={handleAdd}
            className="flex items-center gap-1 rounded border border-accent-cyan/30 bg-accent-cyan/10 px-3 py-1 text-xs font-medium text-accent-cyan hover:bg-accent-cyan/20"
          >
            <Plus className="h-3 w-3" />
            Add
          </button>
          <button
            onClick={onClose}
            className="rounded border border-border px-3 py-1 text-xs text-text-muted hover:bg-surface-raised"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
