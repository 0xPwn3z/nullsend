import { Shield } from "lucide-react";
import { useSessionStore } from "@/store/session";

export function Header() {
  const name = useSessionStore((s) => s.name);
  const provider = useSessionStore((s) => s.provider);
  const model = useSessionStore((s) => s.model);

  return (
    <header className="flex h-12 items-center justify-between border-b border-border bg-surface px-4">
      <div className="flex items-center gap-2">
        <Shield className="h-5 w-5 text-accent-cyan" />
        <span className="font-semibold text-text-primary">SecureRelay</span>
        {name && (
          <span className="ml-2 text-sm text-text-muted">[{name}]</span>
        )}
      </div>
      <div className="flex items-center gap-2 text-xs text-text-muted">
        {provider && (
          <span className="rounded border border-border px-2 py-0.5">
            {provider}/{model}
          </span>
        )}
      </div>
    </header>
  );
}
