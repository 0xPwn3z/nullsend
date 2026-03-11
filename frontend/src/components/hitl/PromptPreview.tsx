import { useState, useRef, useEffect, useCallback, type KeyboardEvent } from "react";
import { ChevronDown, ChevronUp, Search, X, ArrowUp, ArrowDown } from "lucide-react";
import { useHITLStore } from "@/store/hitl";
import { useAnnotatedEditor, type TextSegment } from "@/hooks/useAnnotatedEditor";
import { type EntityType, type ApprovedEntity } from "@/types";
import { cn } from "@/lib/utils";
import { EntityPopover } from "./EntityPopover";

const COLLAPSED_LINES = 5;
const EXPANDED_LINES = 15;
const LINE_HEIGHT = 20; // px approx for monospace text

interface PromptPreviewProps {
  text: string;
}

// ── Helpers for find-match splitting ────────────────────────────

interface FindMatch {
  start: number;
  end: number;
  isActive: boolean;
}

/** Split a segment's content into sub-parts based on find matches that overlap it */
function splitForFind(
  segStart: number,
  segEnd: number,
  content: string,
  matches: FindMatch[],
): { text: string; highlight: "none" | "inactive" | "active" }[] {
  const relevant = matches.filter((m) => m.start < segEnd && m.end > segStart);
  if (relevant.length === 0) return [{ text: content, highlight: "none" }];

  const parts: { text: string; highlight: "none" | "inactive" | "active" }[] = [];
  let cursor = segStart;

  for (const m of relevant) {
    const mStart = Math.max(m.start, segStart);
    const mEnd = Math.min(m.end, segEnd);

    if (mStart > cursor) {
      parts.push({ text: content.slice(cursor - segStart, mStart - segStart), highlight: "none" });
    }
    parts.push({
      text: content.slice(mStart - segStart, mEnd - segStart),
      highlight: m.isActive ? "active" : "inactive",
    });
    cursor = mEnd;
  }

  if (cursor < segEnd) {
    parts.push({ text: content.slice(cursor - segStart), highlight: "none" });
  }

  return parts;
}

// ── Popover state types ─────────────────────────────────────────

interface PopoverState {
  anchorRect: DOMRect;
  mode: "edit" | "add";
  entity?: ApprovedEntity;
  selectedText?: string;
}

// ── Component ───────────────────────────────────────────────────

export function PromptPreview({ text }: PromptPreviewProps) {
  const reviewedEntities = useHITLStore((s) => s.reviewedEntities);
  const detectedEntities = useHITLStore((s) => s.detectedEntities);
  const activeEntityId = useHITLStore((s) => s.activeEntityId);
  const setActiveEntity = useHITLStore((s) => s.setActiveEntity);
  const setEditedText = useHITLStore((s) => s.setEditedText);
  const removeEntity = useHITLStore((s) => s.removeEntity);
  const editEntity = useHITLStore((s) => s.editEntity);
  const addEntity = useHITLStore((s) => s.addEntity);

  const {
    segments,
    findResults,
    activeFindIndex,
    findQuery,
    setFindQuery,
    findNext,
    findPrev,
    clearFind,
  } = useAnnotatedEditor(text, reviewedEntities, detectedEntities, activeEntityId);

  const [isExpanded, setIsExpanded] = useState(false);
  const [showFind, setShowFind] = useState(false);
  const [popover, setPopover] = useState<PopoverState | null>(null);

  const editorRef = useRef<HTMLDivElement>(null);
  const findInputRef = useRef<HTMLInputElement>(null);

  const maxLines = isExpanded ? EXPANDED_LINES : COLLAPSED_LINES;
  const maxHeight = maxLines * LINE_HEIGHT + 24; // + padding

  // Build find matches with isActive flag for rendering
  const findMatches: FindMatch[] = findResults.map((r, i) => ({
    start: r.start,
    end: r.end,
    isActive: i === activeFindIndex,
  }));

  // ── Sync innerHTML from segments (skip if focused to avoid cursor jumps) ──
  useEffect(() => {
    const el = editorRef.current;
    if (!el) return;
    if (document.activeElement === el) return; // don't fight cursor

    el.innerHTML = renderSegmentsToHTML(segments, findMatches, activeEntityId);
  }, [segments, findMatches, activeEntityId]);

  // ── Auto-focus find input when find bar opens ──
  useEffect(() => {
    if (showFind) findInputRef.current?.focus();
  }, [showFind]);

  // ── Scroll active entity span into view ──
  useEffect(() => {
    if (!activeEntityId || !editorRef.current) return;
    const span = editorRef.current.querySelector(
      `[data-entity-id="${CSS.escape(activeEntityId)}"]`,
    ) as HTMLElement | null;
    span?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [activeEntityId]);

  // ── onInput handler for contenteditable ──
  const handleInput = useCallback(() => {
    const el = editorRef.current;
    if (!el) return;
    const newText = el.innerText;
    setEditedText(newText);
  }, [setEditedText]);

  // ── Handle entity click → open edit popover ──
  const handleEditorClick = useCallback(
    (e: React.MouseEvent) => {
      const target = (e.target as HTMLElement).closest("[data-entity-id]") as HTMLElement | null;
      if (target) {
        const id = target.getAttribute("data-entity-id");
        if (id) {
          setActiveEntity(id);
          // Scroll EntityRow into view in the sidebar
          document
            .querySelector(`[data-entity-row-id="${CSS.escape(id)}"]`)
            ?.scrollIntoView({ behavior: "smooth", block: "nearest" });

          // Find the corresponding entity
          const entity = reviewedEntities.find(
            (ent) => `${ent.entity_type}::${ent.original}` === id,
          );
          if (entity) {
            const rect = target.getBoundingClientRect();
            setPopover({ anchorRect: rect, mode: "edit", entity });
          }
        }
      }
    },
    [setActiveEntity, reviewedEntities],
  );

  // ── Handle text selection → add entity popover ──
  const handleEditorMouseUp = useCallback(() => {
    // Small delay to let the selection settle
    requestAnimationFrame(() => {
      const sel = window.getSelection();
      if (!sel || sel.isCollapsed || !editorRef.current) return;

      const selectedText = sel.toString();
      if (selectedText.length < 2) return;

      // Check if selection overlaps an entity span
      const range = sel.getRangeAt(0);
      const container = editorRef.current;

      // Walk through all entity spans — if any intersects the selection range, abort
      const entitySpans = container.querySelectorAll("[data-entity-id]");
      for (const span of entitySpans) {
        if (range.intersectsNode(span)) return;
      }

      // Check that selectedText is a substring of current editedText
      if (!text.includes(selectedText)) return;

      const rect = range.getBoundingClientRect();
      setPopover({ anchorRect: rect, mode: "add", selectedText });
    });
  }, [text]);

  // ── Popover callbacks ──
  const handlePopoverSave = useCallback(
    (patch: Partial<ApprovedEntity>) => {
      if (popover?.mode === "edit" && popover.entity) {
        editEntity(popover.entity.original, {
          original: patch.original,
          entity_type: patch.entity_type,
        });
      } else if (popover?.mode === "add" && patch.original && patch.entity_type) {
        addEntity({
          original: patch.original,
          entity_type: patch.entity_type,
          confidence: patch.confidence ?? 1.0,
        });
      }
      setPopover(null);
      window.getSelection()?.removeAllRanges();
    },
    [popover, editEntity, addEntity],
  );

  const handlePopoverDelete = useCallback(() => {
    if (popover?.entity) {
      removeEntity(popover.entity.original);
    }
    setPopover(null);
  }, [popover, removeEntity]);

  const handlePopoverClose = useCallback(() => {
    setPopover(null);
  }, []);

  // ── Find bar keyboard ──
  const handleFindKeyDown = useCallback(
    (e: KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Escape") {
        clearFind();
        setShowFind(false);
      } else if (e.key === "Enter") {
        if (e.shiftKey) findPrev();
        else findNext();
      }
    },
    [clearFind, findNext, findPrev],
  );

  return (
    <div className="border-b border-border">
      {/* ── Header ── */}
      <div className="flex h-8 items-center justify-between px-4">
        <span className="text-[10px] font-semibold uppercase tracking-wide text-text-muted">
          Prompt Preview
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => {
              setShowFind((v) => !v);
              if (showFind) clearFind();
            }}
            className="rounded p-1 text-text-dim hover:bg-surface-raised hover:text-text-muted"
            title="Find (Ctrl+F)"
          >
            <Search className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setIsExpanded((v) => !v)}
            className="rounded p-1 text-text-dim hover:bg-surface-raised hover:text-text-muted"
            title={isExpanded ? "Collapse" : "Expand"}
          >
            {isExpanded ? (
              <ChevronUp className="h-3.5 w-3.5" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5" />
            )}
          </button>
        </div>
      </div>

      {/* ── Find bar ── */}
      {showFind && (
        <div className="border-b border-[#1e2d45] bg-[#0d1726] px-4 py-2 space-y-1">
          <div className="flex items-center gap-2">
            <Search className="h-3.5 w-3.5 shrink-0 text-text-dim" />
            <input
              ref={findInputRef}
              value={findQuery}
              onChange={(e) => setFindQuery(e.target.value)}
              onKeyDown={handleFindKeyDown}
              placeholder="Search text..."
              className="w-full bg-transparent text-xs text-text-primary placeholder:text-text-dim focus:outline-none font-mono"
            />
          </div>
          <div className="flex items-center gap-2">
            {findQuery.length >= 2 && (
              <span
                className={cn(
                  "text-[10px] tabular-nums",
                  findResults.length === 0
                    ? "text-accent-red"
                    : "text-text-muted",
                )}
              >
                {findResults.length === 0
                  ? "No results"
                  : `${activeFindIndex + 1} / ${findResults.length}`}
              </span>
            )}
            <div className="flex items-center gap-0.5 ml-auto">
              <button
                onClick={findPrev}
                disabled={findResults.length === 0}
                className="rounded p-0.5 text-text-dim hover:bg-surface-raised hover:text-text-muted disabled:opacity-30"
                title="Previous (Shift+Enter)"
              >
                <ArrowUp className="h-3 w-3" />
              </button>
              <button
                onClick={findNext}
                disabled={findResults.length === 0}
                className="rounded p-0.5 text-text-dim hover:bg-surface-raised hover:text-text-muted disabled:opacity-30"
                title="Next (Enter)"
              >
                <ArrowDown className="h-3 w-3" />
              </button>
              <button
                onClick={() => {
                  clearFind();
                  setShowFind(false);
                }}
                className="rounded p-0.5 text-text-dim hover:bg-surface-raised hover:text-text-muted"
                title="Close"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Annotated text editor ── */}
      <div
        ref={editorRef}
        contentEditable
        suppressContentEditableWarning
        onInput={handleInput}
        onClick={handleEditorClick}
        onMouseUp={handleEditorMouseUp}
        className="overflow-y-auto whitespace-pre-wrap border border-[#1e2d45] bg-[#0d1726] p-3 mx-3 mb-3 rounded-[6px] font-mono text-xs text-text-primary focus:outline focus:outline-1 focus:outline-[#00d4ff]"
        style={{
          maxHeight,
          minHeight: maxHeight,
          transition: "max-height 200ms ease, min-height 200ms ease",
          lineHeight: `${LINE_HEIGHT}px`,
        }}
      />

      {/* ── Entity popover (edit or add) ── */}
      {popover && (
        <EntityPopover
          anchorRect={popover.anchorRect}
          mode={popover.mode}
          entity={popover.entity}
          selectedText={popover.selectedText}
          onSave={handlePopoverSave}
          onDelete={popover.mode === "edit" ? handlePopoverDelete : undefined}
          onClose={handlePopoverClose}
        />
      )}
    </div>
  );
}

// ── Static HTML renderer (used to set innerHTML) ────────────────

function highlightClass(hl: "none" | "inactive" | "active"): string {
  if (hl === "active") return "background-color:rgba(250,204,21,0.6);border-radius:2px;";
  if (hl === "inactive") return "background-color:rgba(250,204,21,0.3);border-radius:2px;";
  return "";
}

function entityBgColor(entityType: EntityType): { bg: string; text: string; border: string } {
  const map: Record<EntityType, { bg: string; text: string; border: string }> = {
    IP_ADDRESS:    { bg: "rgba(34,211,238,0.1)",  text: "#22d3ee", border: "#22d3ee" },
    CREDENTIAL:    { bg: "rgba(248,113,113,0.1)", text: "#f87171", border: "#f87171" },
    HOSTNAME:      { bg: "rgba(45,212,191,0.1)",  text: "#2dd4bf", border: "#2dd4bf" },
    NETWORK_RANGE: { bg: "rgba(74,222,128,0.1)",  text: "#4ade80", border: "#4ade80" },
    PORT:          { bg: "rgba(148,163,184,0.1)", text: "#94a3b8", border: "#94a3b8" },
    FILE_PATH:     { bg: "rgba(251,146,60,0.1)",  text: "#fb923c", border: "#fb923c" },
    INTERNAL_CODE: { bg: "rgba(250,204,21,0.1)",  text: "#facc15", border: "#facc15" },
    ORG_NAME:      { bg: "rgba(167,139,250,0.1)", text: "#a78bfa", border: "#a78bfa" },
    PERSON:        { bg: "rgba(251,191,36,0.1)",  text: "#fbbf24", border: "#fbbf24" },
  };
  return map[entityType] ?? { bg: "rgba(148,163,184,0.1)", text: "#94a3b8", border: "#94a3b8" };
}

function escapeHTML(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderSegmentsToHTML(
  segments: TextSegment[],
  findMatches: FindMatch[],
  activeEntityId: string | null,
): string {
  let html = "";

  for (const seg of segments) {
    const parts = splitForFind(seg.start, seg.end, seg.content, findMatches);

    if (seg.type === "text") {
      for (const p of parts) {
        const hl = highlightClass(p.highlight);
        if (hl) {
          html += `<span style="${hl}">${escapeHTML(p.text)}</span>`;
        } else {
          html += escapeHTML(p.text);
        }
      }
    } else {
      // Entity span
      const colors = entityBgColor(seg.entityType!);
      const isActive = seg.entityId === activeEntityId;
      const ringStyle = isActive
        ? `outline:2px solid ${colors.border};outline-offset:1px;`
        : "";
      const baseStyle =
        `background:${colors.bg};color:${colors.text};border-bottom:2px solid ${colors.border};` +
        `cursor:pointer;padding:1px 2px;border-radius:2px;${ringStyle}`;
      const tooltip = `${seg.entityType}  conf: ${seg.confidence?.toFixed(2)}`;

      html += `<span data-entity-id="${escapeHTML(seg.entityId!)}" style="${baseStyle}" title="${escapeHTML(tooltip)}">`;
      for (const p of parts) {
        const hl = highlightClass(p.highlight);
        if (hl) {
          html += `<span style="${hl}">${escapeHTML(p.text)}</span>`;
        } else {
          html += escapeHTML(p.text);
        }
      }
      html += `</span>`;
    }
  }

  return html;
}
