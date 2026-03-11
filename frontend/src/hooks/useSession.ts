import { useCallback } from "react";
import { useSessionStore } from "@/store/session";
import { createSession, deleteSession } from "@/api/session";
import { useConversationStore } from "@/store/conversation";
import { useHITLStore } from "@/store/hitl";

export function useSession() {
  const session = useSessionStore();
  const addMessage = useConversationStore((s) => s.addMessage);
  const clearMessages = useConversationStore((s) => s.clearMessages);
  const resetHitl = useHITLStore((s) => s.reset);

  const startNew = useCallback(
    async (name: string) => {
      if (session.session_id) {
        await deleteSession(session.session_id).catch(() => {});
      }
      clearMessages();
      resetHitl();
      const data = await createSession(name);
      session.setSession({
        session_id: data.session_id,
        name,
        provider: data.provider,
        model: data.model,
        created_at: data.created_at,
        total_input_tokens: 0,
        total_output_tokens: 0,
      });
      addMessage("system", `Session "${name}" started.`);
    },
    [session, addMessage, clearMessages, resetHitl],
  );

  return { ...session, startNew };
}
