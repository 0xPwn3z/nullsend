import { create } from "zustand";
import type { SessionState } from "@/types";

interface SessionActions {
  setSession: (partial: Partial<SessionState>) => void;
  addTokens: (input: number, output: number) => void;
  reset: () => void;
}

const initialState: SessionState = {
  session_id: null,
  name: "",
  provider: "",
  model: "",
  created_at: null,
  total_input_tokens: 0,
  total_output_tokens: 0,
};

export const useSessionStore = create<SessionState & SessionActions>(
  (set) => ({
    ...initialState,

    setSession: (partial) => set((s) => ({ ...s, ...partial })),

    addTokens: (input, output) =>
      set((s) => ({
        total_input_tokens: s.total_input_tokens + input,
        total_output_tokens: s.total_output_tokens + output,
      })),

    reset: () => set(initialState),
  }),
);
