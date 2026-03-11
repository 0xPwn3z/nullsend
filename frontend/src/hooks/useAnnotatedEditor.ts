import { useMemo, useState, useCallback } from "react";
import type { ApprovedEntity, Entity, EntityType } from "@/types";

export interface TextSegment {
  type: "text" | "entity";
  content: string;
  entityId?: string;
  entityType?: EntityType;
  confidence?: number;
  start: number;
  end: number;
}

export interface FindResult {
  start: number;
  end: number;
  index: number;
}

export interface UseAnnotatedEditorReturn {
  segments: TextSegment[];
  findResults: FindResult[];
  activeFindIndex: number;
  findQuery: string;
  setFindQuery: (q: string) => void;
  findNext: () => void;
  findPrev: () => void;
  clearFind: () => void;
}

interface ResolvedSpan {
  start: number;
  end: number;
  original: string;
  entity_type: EntityType;
  confidence: number;
  entityId: string;
}

export function useAnnotatedEditor(
  text: string,
  entities: ApprovedEntity[],
  detectedEntities: Entity[],
  _activeEntityId: string | null,
): UseAnnotatedEditorReturn {
  const [findQuery, setFindQuery] = useState("");
  const [activeFindIndex, setActiveFindIndex] = useState(0);

  // Build segments from text + entities
  const segments = useMemo<TextSegment[]>(() => {
    if (!text) return [];

    // Resolve spans: match reviewedEntities to detectedEntities by original string
    const spans: ResolvedSpan[] = [];

    for (const approved of entities) {
      // Find matching detected entity (has start/end)
      const detected = detectedEntities.find(
        (d) =>
          d.original === approved.original &&
          d.entity_type === approved.entity_type,
      );

      if (detected) {
        // Verify the span still matches the text at that position
        const slice = text.slice(detected.start, detected.end);
        if (slice === approved.original) {
          spans.push({
            start: detected.start,
            end: detected.end,
            original: approved.original,
            entity_type: approved.entity_type,
            confidence: approved.confidence,
            entityId: `${approved.entity_type}::${approved.original}`,
          });
          continue;
        }
      }

      // Fallback: find first occurrence in text (for manually added or shifted entities)
      const idx = text.indexOf(approved.original);
      if (idx !== -1) {
        spans.push({
          start: idx,
          end: idx + approved.original.length,
          original: approved.original,
          entity_type: approved.entity_type,
          confidence: approved.confidence,
          entityId: `${approved.entity_type}::${approved.original}`,
        });
      }
    }

    // Sort by start ascending
    spans.sort((a, b) => a.start - b.start);

    // Remove overlaps: keep higher confidence
    const resolved: ResolvedSpan[] = [];
    for (const span of spans) {
      const last = resolved[resolved.length - 1];
      if (last && span.start < last.end) {
        // Overlap: keep higher confidence
        if (span.confidence > last.confidence) {
          resolved[resolved.length - 1] = span;
        }
        continue;
      }
      resolved.push(span);
    }

    // Build segments
    const result: TextSegment[] = [];
    let cursor = 0;

    for (const span of resolved) {
      if (span.start > cursor) {
        result.push({
          type: "text",
          content: text.slice(cursor, span.start),
          start: cursor,
          end: span.start,
        });
      }
      result.push({
        type: "entity",
        content: text.slice(span.start, span.end),
        entityId: span.entityId,
        entityType: span.entity_type,
        confidence: span.confidence,
        start: span.start,
        end: span.end,
      });
      cursor = span.end;
    }

    if (cursor < text.length) {
      result.push({
        type: "text",
        content: text.slice(cursor),
        start: cursor,
        end: text.length,
      });
    }

    return result;
  }, [text, entities, detectedEntities]);

  // Find results
  const findResults = useMemo<FindResult[]>(() => {
    if (findQuery.length < 2) return [];

    const results: FindResult[] = [];
    const lowerText = text.toLowerCase();
    const lowerQuery = findQuery.toLowerCase();
    let pos = 0;

    while (pos < lowerText.length) {
      const idx = lowerText.indexOf(lowerQuery, pos);
      if (idx === -1) break;
      results.push({
        start: idx,
        end: idx + findQuery.length,
        index: results.length,
      });
      pos = idx + findQuery.length; // non-overlapping
    }

    return results;
  }, [text, findQuery]);

  // Reset activeFindIndex when results change
  const clampedIndex = useMemo(() => {
    if (findResults.length === 0) return 0;
    return activeFindIndex % findResults.length;
  }, [findResults.length, activeFindIndex]);

  const findNext = useCallback(() => {
    if (findResults.length === 0) return;
    setActiveFindIndex((prev) => (prev + 1) % findResults.length);
  }, [findResults.length]);

  const findPrev = useCallback(() => {
    if (findResults.length === 0) return;
    setActiveFindIndex(
      (prev) => (prev - 1 + findResults.length) % findResults.length,
    );
  }, [findResults.length]);

  const clearFind = useCallback(() => {
    setFindQuery("");
    setActiveFindIndex(0);
  }, []);

  return {
    segments,
    findResults,
    activeFindIndex: clampedIndex,
    findQuery,
    setFindQuery: useCallback(
      (q: string) => {
        setFindQuery(q);
        setActiveFindIndex(0);
      },
      [],
    ),
    findNext,
    findPrev,
    clearFind,
  };
}
