// Mirrors backend/app/api/*.py response models.

export type Role = "owner" | "admin" | "marketing" | "sales" | "branch_manager";

export interface Me {
  id: string;
  email: string;
  full_name: string;
  workspaces: { id: string; name: string; role: Role }[];
  is_platform_admin: boolean;
  mfa_enabled: boolean;
}

export interface Billing {
  status: "trial" | "active" | "expired";
  access_until: string;
  price_vnd: number;
  transfer: { bank_bin: string; account: string; account_name: string; content: string; qr_url: string | null };
}

export interface BankTx {
  id: string;
  created_at: string;
  amount_vnd: number;
  content: string;
  reference: string;
  status: "applied" | "unmatched" | "assigned" | "ignored";
  workspace_id: string | null;
  workspace_name: string;
}

export interface AdminWorkspace {
  id: string;
  name: string;
  owner_email: string;
  created_at: string;
  access_until: string;
  active: boolean;
  transfer_code: string;
  paid_total_vnd: number;
}

export interface Workspace {
  id: string;
  name: string;
  timezone: string;
  active_start: string;
  active_end: string;
  reply_mode: "suggest" | "auto";
  auto_reply_min_confidence: number;
  quiet_hours_template: string;
  role: Role;
}

export interface Member {
  user_id: string;
  email: string;
  full_name: string;
  role: Role;
}

export interface Brand {
  name: string;
  industry: string;
  tone_of_voice: string;
  hotline: string;
  address: string;
  opening_hours: string;
  description: string;
  forbidden_claims: string;
}

export interface Branch {
  id: string;
  name: string;
  address: string;
  capacity: number | null;
}

export interface Service {
  id: string;
  name: string;
  description: string;
  duration_minutes: number;
  price_min: number | null;
  price_max: number | null;
  promotion: string;
  active: boolean;
}

export interface Knowledge {
  id: string;
  kind: "faq" | "policy";
  title: string;
  content: string;
}

export interface SocialAccount {
  id: string;
  provider: string;
  external_id: string;
  name: string;
  status: "connected" | "disconnected";
  created_at: string;
}

export type Intent =
  | "price_inquiry"
  | "service_inquiry"
  | "booking_request"
  | "promotion_inquiry"
  | "location_inquiry"
  | "complaint"
  | "other"
  | "spam";

export interface Conversation {
  id: string;
  customer_id: string;
  customer_name: string;
  channel: string;
  status: "open" | "pending" | "resolved";
  assigned_user_id: string | null;
  last_message_at: string | null;
  last_customer_message_at: string | null;
  last_message_preview: string;
  automation_paused: boolean;
  ai_intent: Intent | null;
  ai_confidence: number | null;
  ai_summary: string | null;
  ai_suggested_reply: string | null;
  ai_needs_human: boolean;
  ai_flags: string[];
  ai_updated_at: string | null;
  needs_ai_at: string | null;
}

export interface Message {
  id: string;
  direction: "in" | "out";
  actor: "customer" | "human" | "ai" | "system";
  text: string;
  provider_status: string;
  error: string | null;
  created_at: string;
}

export interface Decision {
  id: string;
  decision: "ALLOW" | "HOLD" | "SKIP";
  reasons: string[];
  purpose: string;
  actor: string;
  hold_until: string | null;
  created_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
  decisions: Decision[];
}

export type LeadStatus =
  | "new"
  | "engaged"
  | "interested"
  | "qualified"
  | "booking_pending"
  | "booked"
  | "not_interested"
  | "opted_out";

export interface Lead {
  id: string;
  customer_id: string;
  source: string;
  status: LeadStatus;
  score: number;
  interested_service_id: string | null;
  created_at: string;
}

export interface Customer {
  id: string;
  display_name: string;
  phone: string | null;
  email: string | null;
  tags: string[];
  notes: string;
  consent_marketing: boolean;
  last_interaction_at: string | null;
  opted_out_at: string | null;
  created_at: string;
}

export interface Customer360 extends Customer {
  suppressed: boolean;
  channels: string[];
  leads: Lead[];
  bookings: {
    id: string;
    service_id: string;
    branch_id: string;
    start_at: string;
    status: BookingStatus;
    expected_value: number | null;
    actual_revenue: number | null;
  }[];
  conversation_ids: string[];
}

export type BookingStatus =
  | "pending"
  | "confirmed"
  | "arrived"
  | "completed"
  | "cancelled"
  | "no_show";

export interface Booking {
  id: string;
  customer_id: string;
  customer_name: string;
  branch_id: string;
  service_id: string;
  service_name: string;
  conversation_id: string | null;
  start_at: string;
  end_at: string;
  status: BookingStatus;
  source: string;
  expected_value: number | null;
  actual_revenue: number | null;
  notes: string;
  created_at: string;
}

export interface Notification {
  id: string;
  type: string;
  priority: string;
  title: string;
  body: string;
  conversation_id: string | null;
  customer_id: string | null;
  read_at: string | null;
  created_at: string;
}

export interface Overview {
  period_start: string;
  period_end: string;
  leads_total: number;
  leads_by_source: Record<string, number>;
  leads_by_status: Record<string, number>;
  conversations: number;
  conversations_replied: number;
  response_rate: number | null;
  avg_first_response_minutes: number | null;
  needs_human: number;
  bookings_total: number;
  bookings_by_status: Record<string, number>;
  lead_to_booking_rate: number | null;
  expected_revenue: number;
  actual_revenue: number;
  unread_high_intent: number;
}

export interface Today {
  date: string;
  timezone: string;
  active_start: string;
  active_end: string;
  inbound_by_hour: number[];
  queued_for_morning: number;
  next_batch_at: string | null;
}

// ---------- Project Creative Workspace (backend app/creative) ----------

export type ArtifactKind = "research" | "script" | "image" | "video" | "short";
export type ArtifactStatus = "generating" | "ready" | "selected" | "approved" | "failed" | "archived";

export interface ProjectContext {
  summary: string;
  services: string[];
  key_messages: string[];
  brand_voice: string;
  audience: string;
  key_facts: { fact: string; source: string }[];
  constraints: string[];
  missing: string[];
}

export interface Project {
  id: string;
  name: string;
  objective: string;
  service_id: string | null;
  audience: string;
  location: string;
  start_date: string | null;
  end_date: string | null;
  brief: string;
  research_urls: string[];
  status: "draft" | "active" | "archived" | "deleted";
  context: ProjectContext | null;
  context_confirmed_at: string | null;
  deleted_at: string | null;
  created_at: string;
  counts: Partial<Record<ArtifactKind, number>>;
  storage_bytes: number;
  cover_url: string | null;
}

export interface ProjectInput {
  id: string;
  role: string;
  title: string;
  description: string;
  usage_confirmed: boolean;
  preserve: boolean;
  filename: string;
  mime_type: string;
  byte_size: number;
  url: string;
  created_at: string;
}

export interface Shot {
  description: string;
  visual_prompt: string;
  motion: string;
  on_screen_text: string;
  voiceover?: string;
  framing?: string;
  transition?: string;
  stat?: string;
  sfx: string;
  duration_seconds: number;
}

export interface Script {
  title: string;
  angle: string;
  insight: string;
  hook: string;
  key_message: string;
  cta: string;
  duration_seconds: number;
  voiceover: string;
  music_mood: string;
  caption: string;
  hashtags: string[];
  continuity?: { product: string; talent: string; setting: string; motif?: string };
  shots: Shot[];
  flags?: string[];
  instruction?: string;
}

export interface ResearchReport {
  research_summary: string;
  target_audience: string[];
  customer_pain_points: string[];
  customer_questions: string[];
  competitor_insights: string[];
  social_trends: string[];
  content_opportunities: string[];
  evidence: { claim: string; source_url: string; source_title: string }[];
  assumptions: string[];
  counterexamples: string[];
  risks: string[];
  unknowns: string[];
  confidence: "low" | "medium" | "high";
  sources: { index: number; url: string; title: string }[];
  source_mode: "provided_urls" | "google_search";
  unreachable_sources: string[];
  mode: string;
}

export interface ArtifactVersion {
  id: string;
  version_number: number;
  parent_version_id: string | null;
  content: Record<string, unknown>;
  actor: string;
  provider: string | null;
  model: string | null;
  media_job_id: string | null;
  created_at: string;
  url: string | null;
  mime_type: string | null;
  byte_size: number | null;
}

export interface Artifact {
  id: string;
  kind: ArtifactKind;
  display_name: string;
  variant_key: string | null;
  status: ArtifactStatus;
  pinned: boolean;
  error: string | null;
  created_at: string;
  updated_at: string | null;
  current: ArtifactVersion | null;
  version_count: number;
}

export interface ArtifactDetail extends Artifact {
  versions: ArtifactVersion[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  artifact_id: string | null;
  action: { type: string; artifact_ids?: string[]; script_artifact_id?: string; note?: string } | null;
  created_at: string;
}

export interface MediaJob {
  id: string;
  kind: "studio" | "shorts";
  status: "preparing" | "queued" | "running" | "succeeded" | "failed" | "cancelled";
  stage: string;
  progress: number;
  attempts: number;
  error: string | null;
  created_at: string;
  finished_at: string | null;
  prompt_snapshot: Record<string, unknown>;
}

export interface StyleBlock {
  id?: string;
  name: string;
  category: string;
  content: string;
  priority: number;
  applies_to: ("image" | "video" | "audio")[];
  enabled: boolean;
}

export interface StylePack {
  id: string;
  name: string;
  description: string;
  status: string;
  is_preset: boolean;
  version_id: string | null;
  version_number: number | null;
  blocks: StyleBlock[];
  created_at: string;
}

export interface EffectiveStyle {
  source: "project" | "workspace" | "platform" | "none" | "preview";
  pack_id: string | null;
  pack_name: string | null;
  version_id: string | null;
  version_number: number | null;
}

export interface PublishingJob {
  id: string;
  project_id: string | null;
  social_account_id: string;
  artifact_version_id: string;
  media_type: "photo" | "video";
  caption: string;
  scheduled_at: string;
  timezone: string;
  status: "scheduled" | "publishing" | "published" | "failed" | "cancelled";
  external_post_id: string | null;
  published_at: string | null;
  attempts: number;
  last_error: string | null;
  created_at: string;
  page_name: string;
  artifact_name: string;
}
