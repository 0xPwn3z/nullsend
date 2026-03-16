import { useState, useRef, useCallback, useEffect } from "react";
import { Header } from "./Header";
import { StatusBar } from "./StatusBar";
import { ConversationFeed } from "@/components/conversation/ConversationFeed";
import { PromptInput } from "@/components/input/PromptInput";
import { HITLSidebar } from "@/components/hitl/HITLSidebar";

const STORAGE_KEY = "nullsend:sidebar-width";
const MIN_SIDEBAR = 280;
const MAX_SIDEBAR = 600;
const MIN_CONVERSATION = 400;

function loadSidebarWidth(): number {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const n = Number(stored);
      if (n >= MIN_SIDEBAR && n <= MAX_SIDEBAR) return n;
    }
  } catch {
    // ignore
  }
  // Default: 28% of viewport, clamped
  const def = Math.round(window.innerWidth * 0.28);
  return Math.max(MIN_SIDEBAR, Math.min(MAX_SIDEBAR, def));
}

export function AppLayout() {
  const [sidebarWidth, setSidebarWidth] = useState(loadSidebarWidth);
  const dragging = useRef(false);

  // Persist sidebar width to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, String(sidebarWidth));
    } catch {
      // ignore
    }
  }, [sidebarWidth]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    dragging.current = true;

    // Disable text selection during drag
    document.body.classList.add("select-none");

    const handleMouseMove = (ev: MouseEvent) => {
      if (!dragging.current) return;
      requestAnimationFrame(() => {
        const totalWidth = window.innerWidth;
        // sidebarWidth = distance from right edge to mouse
        let newWidth = totalWidth - ev.clientX;
        // Clamp: min sidebar
        newWidth = Math.max(MIN_SIDEBAR, newWidth);
        // Clamp: max sidebar
        newWidth = Math.min(MAX_SIDEBAR, newWidth);
        // Clamp: ensure conversation keeps min width
        if (totalWidth - newWidth < MIN_CONVERSATION) {
          newWidth = totalWidth - MIN_CONVERSATION;
        }
        // Final safety clamp
        newWidth = Math.max(MIN_SIDEBAR, newWidth);
        setSidebarWidth(newWidth);
      });
    };

    const handleMouseUp = () => {
      dragging.current = false;
      document.body.classList.remove("select-none");
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
  }, []);

  return (
    <div className="flex h-screen flex-col bg-screen">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        {/* Main content area */}
        <div className="flex flex-1 flex-col overflow-hidden" style={{ minWidth: MIN_CONVERSATION }}>
          <ConversationFeed />
          <PromptInput />
        </div>

        {/* Drag handle */}
        <div
          onMouseDown={handleMouseDown}
          className="group flex-shrink-0 cursor-col-resize"
          style={{ width: 4 }}
        >
          <div className="h-full w-full bg-[#1e2d45] transition-colors duration-150 group-hover:bg-[#00d4ff] group-active:bg-[#00d4ff] group-hover:shadow-[0_0_8px_#00d4ff55] group-active:shadow-[0_0_8px_#00d4ff55]" />
        </div>

        {/* HITL sidebar – resizable */}
        <div style={{ width: sidebarWidth, flexShrink: 0 }} className="overflow-hidden">
          <HITLSidebar />
        </div>
      </div>
      <StatusBar />
    </div>
  );
}
