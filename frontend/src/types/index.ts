// ── Entity types ─────────────────────────────────────────────────

export type EntityType =
  | "IP_ADDRESS"
  | "HOSTNAME"
  | "CREDENTIAL"
  | "NETWORK_RANGE"
  | "PORT"
  | "FILE_PATH"
  | "INTERNAL_CODE"
  | "ORG_NAME"
  | "PERSON";

export interface Entity {
  original: string;
  entity_type: EntityType;
  start: number;
  end: number;
  confidence: number;
}

export interface ApprovedEntity {
  original: string;
  entity_type: EntityType;
  confidence: number;
}

// ── Messages ────────────────────────────────────────────────────

export type MessageRole = "user" | "assistant" | "system" | "error";

export interface MessageMetadata {
  entity_count?: number;
  entities_removed?: number;
  entities_added?: number;
  input_tokens?: number;
  output_tokens?: number;
  safe_text?: string;
  isStreaming?: boolean;
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  metadata?: MessageMetadata;
}

// ── Session ─────────────────────────────────────────────────────

export interface SessionState {
  session_id: string | null;
  name: string;
  provider: string;
  model: string;
  created_at: string | null;
  total_input_tokens: number;
  total_output_tokens: number;
}

// ── HITL ────────────────────────────────────────────────────────

export type HITLStatus = "idle" | "reviewing" | "approved" | "cancelled";

export interface HITLState {
  isOpen: boolean;
  originalText: string;
  detectedEntities: Entity[];
  reviewedEntities: ApprovedEntity[];
  status: HITLStatus;
  safeText: string;
}

// ── Vault ───────────────────────────────────────────────────────

export interface VaultToken {
  token_id: string;
  entity_type: EntityType;
  original_value: string;
  created_at: string;
  revealed: boolean;
}

// ── API types ───────────────────────────────────────────────────

export interface NewSessionResponse {
  session_id: string;
  created_at: string;
  provider: string;
  model: string;
}

export interface AnalyzeResponse {
  session_id: string;
  original_text: string;
  entities: Entity[];
}

export interface SendRequestBody {
  session_id: string;
  original_text: string;
  approved_entities: ApprovedEntity[];
}

export interface DoneEventData {
  restored_response: string;
  input_tokens: number;
  output_tokens: number;
  safe_text: string;
}

export interface VaultResponse {
  tokens: Omit<VaultToken, "revealed">[];
}

// ── Entity color map ────────────────────────────────────────────

export const ENTITY_COLORS: Record<EntityType, string> = {
  IP_ADDRESS:    "text-cyan-400 bg-cyan-400/10 border-cyan-400/30",
  CREDENTIAL:    "text-red-400 bg-red-400/10 border-red-400/30",
  HOSTNAME:      "text-teal-400 bg-teal-400/10 border-teal-400/30",
  NETWORK_RANGE: "text-green-400 bg-green-400/10 border-green-400/30",
  PORT:          "text-slate-400 bg-slate-400/10 border-slate-400/30",
  FILE_PATH:     "text-orange-400 bg-orange-400/10 border-orange-400/30",
  INTERNAL_CODE: "text-yellow-400 bg-yellow-400/10 border-yellow-400/30",
  ORG_NAME:      "text-violet-400 bg-violet-400/10 border-violet-400/30",
  PERSON:        "text-amber-400 bg-amber-400/10 border-amber-400/30",
};

export const ALL_ENTITY_TYPES: EntityType[] = [
  "IP_ADDRESS",
  "HOSTNAME",
  "CREDENTIAL",
  "NETWORK_RANGE",
  "PORT",
  "FILE_PATH",
  "INTERNAL_CODE",
  "ORG_NAME",
  "PERSON",
];
