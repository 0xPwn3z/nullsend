import { useSessionStore } from "@/store/session";
import { useConversationStore } from "@/store/conversation";
import { useHITLStore } from "@/store/hitl";

export function StatusBar() {
  const totalIn = useSessionStore((s) => s.total_input_tokens);
  const totalOut = useSessionStore((s) => s.total_output_tokens);
  const provider = useSessionStore((s) => s.provider);
  const messages = useConversationStore((s) => s.messages);
  const reviewedCount = useHITLStore((s) => s.reviewedEntities.length);

  const entityCount = messages.reduce(
    (acc, m) => acc + (m.metadata?.entity_count ?? 0),
    0,
  );

  return (
    <footer className="flex h-8 items-center justify-between border-t border-border bg-surface px-4 text-xs text-text-muted">
      <div className="flex gap-4">
        <span>
          Tokens: {totalIn} in / {totalOut} out
        </span>
        <span>Entities anonymized: {entityCount}</span>
        {reviewedCount > 0 && (
          <span className="text-accent-amber">
            Reviewing: {reviewedCount}
          </span>
        )}
      </div>
      <span>{provider}</span>
    </footer>
  );
}
