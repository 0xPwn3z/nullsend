import { useVault } from "@/hooks/useVault";
import { TokenRow } from "./TokenRow";

export function VaultPanel() {
  const { data, isLoading, error } = useVault();

  if (isLoading) {
    return (
      <div className="p-4 text-xs text-text-dim">Loading vault...</div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-xs text-accent-red">
        Failed to load vault.
      </div>
    );
  }

  const tokens = data?.tokens ?? [];

  if (tokens.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-1 p-8 text-center">
        <p className="text-xs text-text-muted">No tokens yet.</p>
        <p className="text-[10px] text-text-dim">
          Tokens appear here after you send an anonymized prompt.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2 p-3">
      <p className="text-[10px] uppercase tracking-wide text-text-dim">
        {tokens.length} token{tokens.length !== 1 ? "s" : ""}
      </p>
      {tokens.map((t) => (
        <TokenRow
          key={t.token_id}
          tokenId={t.token_id}
          entityType={t.entity_type}
          originalValue={t.original_value}
          createdAt={t.created_at}
        />
      ))}
    </div>
  );
}
