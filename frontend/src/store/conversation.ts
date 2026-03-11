import { create } from "zustand";
import type { Message, MessageRole, MessageMetadata } from "@/types";

interface ConversationState {
  messages: Message[];
}

interface ConversationActions {
  addMessage: (
    role: MessageRole,
    content: string,
    metadata?: MessageMetadata,
  ) => string;
  updateMessage: (id: string, patch: Partial<Message>) => void;
  clearMessages: () => void;
}

let _counter = 0;

export const useConversationStore = create<
  ConversationState & ConversationActions
>((set) => ({
  messages: [],

  addMessage: (role, content, metadata) => {
    const id = `msg_${Date.now()}_${++_counter}`;
    const message: Message = {
      id,
      role,
      content,
      timestamp: new Date(),
      metadata,
    };
    set((s) => ({ messages: [...s.messages, message] }));
    return id;
  },

  updateMessage: (id, patch) =>
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === id ? { ...m, ...patch } : m,
      ),
    })),

  clearMessages: () => set({ messages: [] }),
}));
