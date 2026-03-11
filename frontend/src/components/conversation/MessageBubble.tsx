import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChevronDown, ChevronUp } from "lucide-react";
import type { Message } from "@/types";

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const [expanded, setExpanded] = useState(false);
  const { role, content, metadata } = message;

  if (role === "system") {
    return (
      <div className="flex w-full justify-center px-4 py-2">
        <span className="text-xs italic text-text-muted">{content}</span>
      </div>
    );
  }

  if (role === "error") {
    return (
      <div className="flex w-full justify-start px-4 py-2">
        <div className="max-w-[75%] rounded border-l-2 border-accent-red bg-red-400/5 p-4 text-sm text-accent-red">
          {content}
        </div>
      </div>
    );
  }

  if (role === "user") {
    return (
      <div className="flex w-full justify-end px-4 py-2">
        <div className="max-w-[75%]">
          <div className="rounded border border-border bg-surface-raised p-4 text-sm text-text-primary">
            {content}
          </div>
          {metadata?.entity_count != null && metadata.entity_count > 0 && (
            <div className="mt-1 flex flex-wrap justify-end gap-1">
              <span className="text-xs text-text-muted">
                {metadata.entity_count} entities anonymized
              </span>
            </div>
          )}
        </div>
      </div>
    );
  }

  // assistant
  return (
    <div className="flex w-full justify-start px-4 py-2">
      <div className="max-w-[75%]">
        <div className="rounded border border-border bg-surface p-4">
          <div className="prose prose-invert prose-sm max-w-none text-sm">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {content}
            </ReactMarkdown>
          </div>
        </div>
        <div className="mt-1 flex items-center justify-between text-xs text-text-muted">
          <div className="flex gap-2">
            {metadata?.input_tokens != null && (
              <span>
                ↑ {metadata.input_tokens} ↓ {metadata.output_tokens}
              </span>
            )}
          </div>
          {metadata?.safe_text && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-1 text-text-dim hover:text-text-muted"
            >
              {expanded ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
              Anonymized prompt
            </button>
          )}
        </div>
        {expanded && metadata?.safe_text && (
          <div className="mt-2 rounded border border-border bg-screen p-3 font-mono text-xs text-text-dim">
            {metadata.safe_text}
          </div>
        )}
      </div>
    </div>
  );
}
