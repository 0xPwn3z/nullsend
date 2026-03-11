import { create } from "zustand";
import type { Entity, ApprovedEntity, EntityType, HITLStatus } from "@/types";

interface HITLStoreState {
  isOpen: boolean;
  originalText: string;
  editedText: string;
  activeEntityId: string | null;
  detectedEntities: Entity[];
  reviewedEntities: ApprovedEntity[];
  status: HITLStatus;
  safeText: string;
}

interface HITLActions {
  openReview: (text: string, entities: Entity[]) => void;
  approveEntity: (entity: ApprovedEntity) => void;
  removeEntity: (original: string) => void;
  editEntity: (
    original: string,
    patch: { original?: string; entity_type?: EntityType },
  ) => void;
  addEntity: (entity: ApprovedEntity) => void;
  approveAll: () => void;
  cancel: () => void;
  reset: () => void;
  setSafeText: (text: string) => void;
  setStatus: (status: HITLStatus) => void;
  setEditedText: (text: string) => void;
  setActiveEntity: (id: string | null) => void;
}

const initialState: HITLStoreState = {
  isOpen: false,
  originalText: "",
  editedText: "",
  activeEntityId: null,
  detectedEntities: [],
  reviewedEntities: [],
  status: "idle",
  safeText: "",
};

export const useHITLStore = create<HITLStoreState & HITLActions>((set) => ({
  ...initialState,

  openReview: (text, entities) =>
    set({
      isOpen: true,
      originalText: text,
      editedText: text,
      activeEntityId: null,
      detectedEntities: entities,
      reviewedEntities: entities.map((e) => ({
        original: e.original,
        entity_type: e.entity_type,
        confidence: e.confidence,
      })),
      status: "reviewing",
      safeText: "",
    }),

  approveEntity: (entity) =>
    set((s) => ({
      reviewedEntities: [...s.reviewedEntities, entity],
    })),

  removeEntity: (original) =>
    set((s) => ({
      reviewedEntities: s.reviewedEntities.filter(
        (e) => e.original !== original,
      ),
    })),

  editEntity: (original, patch) =>
    set((s) => ({
      reviewedEntities: s.reviewedEntities.map((e) =>
        e.original === original ? { ...e, ...patch } : e,
      ),
    })),

  addEntity: (entity) =>
    set((s) => ({
      reviewedEntities: [...s.reviewedEntities, entity],
    })),

  approveAll: () => set({ status: "approved" }),

  cancel: () => set({ status: "cancelled", isOpen: false }),

  reset: () => set(initialState),

  setSafeText: (text) => set({ safeText: text }),

  setStatus: (status) => set({ status }),

  setEditedText: (text) =>
    set((s) => ({
      editedText: text,
      reviewedEntities: s.reviewedEntities.filter((e) =>
        text.includes(e.original),
      ),
    })),

  setActiveEntity: (id) => set({ activeEntityId: id }),
}));
