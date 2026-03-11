import { useQuery } from "@tanstack/react-query";
import { fetchVaultTokens } from "@/api/vault";
import { useSessionStore } from "@/store/session";

export function useVault() {
  const sessionId = useSessionStore((s) => s.session_id);

  return useQuery({
    queryKey: ["vault", sessionId],
    queryFn: () => fetchVaultTokens(sessionId!),
    enabled: !!sessionId,
    refetchInterval: 5000,
  });
}
