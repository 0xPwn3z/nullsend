import { useEffect } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { useSessionStore } from "@/store/session";
import { createSession } from "@/api/session";

export default function App() {
  const setSession = useSessionStore((s) => s.setSession);
  const sessionId = useSessionStore((s) => s.session_id);

  useEffect(() => {
    if (sessionId) return;
    createSession("default").then((data) => {
      setSession({
        session_id: data.session_id,
        name: "default",
        provider: data.provider,
        model: data.model,
        created_at: data.created_at,
      });
    });
  }, [sessionId, setSession]);

  return <AppLayout />;
}
