import { useState, useEffect } from "react";
import { Lock, Loader2, ShieldCheck, Vault as VaultIcon, ChevronRight, ChevronDown } from "lucide-react";
import { useHITLStore } from "@/store/hitl";
import { EntityRow } from "./EntityRow";
import { HITLEmptyState } from "./HITLEmptyState";
import { VaultPanel } from "@/components/vault/VaultPanel";
import { PromptPreview } from "./PromptPreview";
import { ENTITY_COLORS, type EntityType } from "@/types";

// ── Type abbreviation map ───────────────────────────────────────
const TYPE_ABBR: Record<EntityType, string> = {
  IP_ADDRESS: "IP",
  HOSTNAME: "HOST",
  CREDENTIAL: "CRED",
  NETWORK_RANGE: "NET",
  PORT: "PORT",
  FILE_PATH: "PATH",
  INTERNAL_CODE: "CODE",
  ORG_NAME: "ORG",
  PERSON: "PERSON",
};

// Dot colors extracted from ENTITY_COLORS (just the text color portion)
const DOT_COLORS: Record<EntityType, string> = {
  IP_ADDRESS: "#22d3ee",
  CREDENTIAL: "#f87171",
  HOSTNAME: "#2dd4bf",
  NETWORK_RANGE: "#4ade80",
  PORT: "#94a3b8",
  FILE_PATH: "#fb923c",
  INTERNAL_CODE: "#facc15",
  ORG_NAME: "#a78bfa",
  PERSON: "#fbbf24",
};

export function HITLSidebar() {
  const status = useHITLStore((s) => s.status);
  const reviewedEntities = useHITLStore((s) => s.reviewedEntities);
  const editedText = useHITLStore((s) => s.editedText);
  const activeEntityId = useHITLStore((s) => s.activeEntityId);
  const safeText = useHITLStore((s) => s.safeText);
  const approveAll = useHITLStore((s) => s.approveAll);
  const cancel = useHITLStore((s) => s.cancel);
  const setActiveEntity = useHITLStore((s) => s.setActiveEntity);

  const [entitiesExpanded, setEntitiesExpanded] = useState(false);

  // Scroll active EntityRow into view when activeEntityId changes
  useEffect(() => {
    if (!activeEntityId) return;
    document
      .querySelector(`[data-entity-row-id="${CSS.escape(activeEntityId)}"]`)
      ?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [activeEntityId]);

  // ── Compute type counts for badges ──
  const typeCounts = reviewedEntities.reduce<Record<string, number>>((acc, e) => {
    acc[e.entity_type] = (acc[e.entity_type] || 0) + 1;
    return acc;
  }, {});

  const typeEntries = Object.entries(typeCounts) as [EntityType, number][];

  // IDLE: show vault
  if (status === "idle" || status === "cancelled") {
    return (
      <aside className="flex h-full flex-shrink-0 flex-col border-l border-border bg-surface">
        <div className="flex h-10 items-center gap-2 border-b border-border px-4">
          <VaultIcon className="h-4 w-4 text-accent-cyan" />
          <span className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            Vault
          </span>
        </div>
        <div className="flex-1 overflow-y-auto">
          <VaultPanel />
        </div>
      </aside>
    );
  }

  // STREAMING / APPROVED: show sending state
  if (status === "approved") {
    return (
      <aside className="flex h-full flex-shrink-0 flex-col border-l border-border bg-surface">
        <div className="flex h-10 items-center gap-2 border-b border-border px-4">
          <Loader2 className="h-4 w-4 animate-spin text-accent-cyan" />
          <span className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            Sending — anonymized
          </span>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          <p className="text-xs text-text-muted">
            Sending anonymized prompt...
          </p>
          {safeText && (
            <pre className="mt-3 whitespace-pre-wrap rounded border border-border bg-screen p-3 font-mono text-xs text-text-dim">
              {safeText}
            </pre>
          )}
        </div>
      </aside>
    );
  }

  // REVIEWING
  return (
    <aside className="flex h-full flex-shrink-0 flex-col border-l border-border bg-surface">
      {/* Header */}
      <div className="flex h-10 items-center gap-2 border-b border-border px-4">
        <ShieldCheck className="h-4 w-4 text-accent-amber" />
        <span className="text-xs font-semibold uppercase tracking-wide text-text-muted">
          Review — {reviewedEntities.length} entities
        </span>
      </div>

      {/* Prompt preview */}
      <PromptPreview text={editedText} />

      {/* ── Collapsible entity recap ── */}
      <div className="border-b border-border">
        {/* Recap header — always visible, clickable */}
        <button
          onClick={() => setEntitiesExpanded((v) => !v)}
          className="flex w-full items-center gap-2 px-3 py-2 hover:bg-surface-raised transition-colors"
        >
          {entitiesExpanded ? (
            <ChevronDown className="h-3.5 w-3.5 text-text-dim flex-shrink-0" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5 text-text-dim flex-shrink-0" />
          )}
          <span className="text-[10px] font-semibold uppercase tracking-wide text-text-muted whitespace-nowrap">
            Entities — {reviewedEntities.length}
          </span>
          <div className="flex items-center gap-1.5 ml-auto overflow-hidden">
            {(typeEntries.length <= 5
              ? typeEntries
              : typeEntries.slice(0, 4)
            ).map(([type, count]) => (
              <span
                key={type}
                className="flex items-center gap-1 text-[10px] text-text-dim whitespace-nowrap"
              >
                <span
                  className="inline-block h-2 w-2 rounded-full flex-shrink-0"
                  style={{ backgroundColor: DOT_COLORS[type] }}
                />
                {TYPE_ABBR[type]}×{count}
              </span>
            ))}
            {typeEntries.length > 5 && (
              <span className="text-[10px] text-text-dim whitespace-nowrap">
                +{typeEntries.length - 4} more
              </span>
            )}
          </div>
        </button>

        {/* Entity list — animated collapse */}
        <div
          style={{
            maxHeight: entitiesExpanded ? 240 : 0,
            transition: "max-height 200ms ease",
          }}
          className="overflow-hidden"
        >
          <div className="overflow-y-auto p-3 space-y-2" style={{ maxHeight: 240 }}>
            {reviewedEntities.length === 0 && <HITLEmptyState />}
            {reviewedEntities.map((entity) => {
              const entityId = `${entity.entity_type}::${entity.original}`;
              return (
                <div
                  key={entity.original}
                  data-entity-row-id={entityId}
                  onClick={() => setActiveEntity(entityId)}
                  className={`cursor-pointer rounded transition-colors duration-150 ${
                    activeEntityId === entityId
                      ? "border-l-2 border-l-[#00d4ff] bg-[#112035]"
                      : ""
                  }`}
                >
                  <EntityRow entity={entity} />
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Spacer to push action bar down */}
      <div className="flex-1" />

      {/* Action bar */}
      <div className="flex items-center justify-between border-t border-border p-3">
        <button
          onClick={cancel}
          className="rounded border border-border px-3 py-1.5 text-xs text-text-muted hover:bg-surface-raised"
        >
          Cancel
        </button>
        <button
          onClick={approveAll}
          className="flex items-center gap-1.5 rounded border border-accent-cyan/30 bg-accent-cyan/10 px-4 py-1.5 text-xs font-medium text-accent-cyan hover:bg-accent-cyan/20"
        >
          <Lock className="h-3.5 w-3.5" />
          Approve & Send
        </button>
      </div>
    </aside>
  );
}
