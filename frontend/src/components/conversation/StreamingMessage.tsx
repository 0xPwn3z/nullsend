import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface StreamingMessageProps {
  content: string;
}

export function StreamingMessage({ content }: StreamingMessageProps) {
  return (
    <div className="flex w-full justify-start px-4 py-2">
      <div className="max-w-[75%] rounded border border-border bg-surface p-4">
        <div className="prose prose-invert prose-sm max-w-none font-mono text-sm">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {content}
          </ReactMarkdown>
          <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse bg-accent-cyan" />
        </div>
      </div>
    </div>
  );
}
