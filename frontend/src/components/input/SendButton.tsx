import { Send } from "lucide-react";

interface SendButtonProps {
  disabled: boolean;
  onClick: () => void;
}

export function SendButton({ disabled, onClick }: SendButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded border border-accent-cyan/30 bg-accent-cyan/10 text-accent-cyan transition-colors hover:bg-accent-cyan/20 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-accent-cyan/10"
    >
      <Send className="h-4 w-4" />
    </button>
  );
}
