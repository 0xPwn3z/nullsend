import { useEffect, useRef, useCallback, useState } from "react";
import { ArrowDown } from "lucide-react";
import { useConversationStore } from "@/store/conversation";
import { useSessionStore } from "@/store/session";
import { useHITLStore } from "@/store/hitl";
import { useStream } from "@/hooks/useStream";
import { MessageBubble } from "./MessageBubble";
import { StreamingMessage } from "./StreamingMessage";
import { ThinkingIndicator } from "./ThinkingIndicator";
import type { DoneEventData } from "@/types";

export function ConversationFeed() {
  const messages = useConversationStore((s) => s.messages);
  const addMessage = useConversationStore((s) => s.addMessage);
  const sessionId = useSessionStore((s) => s.session_id);
  const addTokens = useSessionStore((s) => s.addTokens);
  const hitlStatus = useHITLStore((s) => s.status);
  const originalText = useHITLStore((s) => s.originalText);
  const editedText = useHITLStore((s) => s.editedText);
  const reviewedEntities = useHITLStore((s) => s.reviewedEntities);
  const resetHitl = useHITLStore((s) => s.reset);
  const setSafeText = useHITLStore((s) => s.setSafeText);
  const setHitlStatus = useHITLStore((s) => s.setStatus);

  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [isWaiting, setIsWaiting] = useState(false);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
    setShowScrollBtn(!atBottom);
  }, []);

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  // Stream handler
  const handleChunk = useCallback((chunk: string) => {
    setStreamingContent((prev) => prev + chunk);
    setIsWaiting(false);
  }, []);

  const handleDone = useCallback(
    (data: DoneEventData) => {
      setStreamingContent("");
      setIsWaiting(false);
      addMessage("assistant", data.restored_response, {
        input_tokens: data.input_tokens,
        output_tokens: data.output_tokens,
        safe_text: data.safe_text,
      });
      addTokens(data.input_tokens, data.output_tokens);
      resetHitl();
    },
    [addMessage, addTokens, resetHitl],
  );

  const handleError = useCallback(
    (message: string) => {
      setStreamingContent("");
      setIsWaiting(false);
      addMessage("error", message);
      resetHitl();
    },
    [addMessage, resetHitl],
  );

  const { startStream, isStreaming } = useStream({
    onChunk: handleChunk,
    onDone: handleDone,
    onError: handleError,
  });

  // React to HITL approval
  useEffect(() => {
    if (hitlStatus !== "approved" || !sessionId) return;
    setHitlStatus("idle");

    const textToSend = editedText !== originalText ? editedText : originalText;

    // Add user message
    addMessage("user", textToSend, {
      entity_count: reviewedEntities.length,
    });

    setIsWaiting(true);

    startStream({
      session_id: sessionId,
      original_text: textToSend,
      approved_entities: reviewedEntities,
    });
  }, [
    hitlStatus,
    sessionId,
    originalText,
    editedText,
    reviewedEntities,
    startStream,
    addMessage,
    setHitlStatus,
    setSafeText,
  ]);

  return (
    <div
      ref={scrollRef}
      onScroll={handleScroll}
      className="relative flex-1 overflow-y-auto"
    >
      <div className="flex flex-col py-4">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isWaiting && !isStreaming && <ThinkingIndicator />}
        {isStreaming && streamingContent && (
          <StreamingMessage content={streamingContent} />
        )}
        <div ref={bottomRef} />
      </div>

      {showScrollBtn && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full border border-border bg-surface p-2 shadow-lg hover:bg-surface-raised"
        >
          <ArrowDown className="h-4 w-4 text-text-muted" />
        </button>
      )}
    </div>
  );
}
