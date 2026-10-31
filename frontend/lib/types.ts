// Mirrors backend/app/api/*.py response models.

export type Role = "owner" | "admin" | "marketing" | "sales" | "branch_manager";

export interface Me {
  id: string;
  email: string;
  full_name: string;
  workspaces: { id: string; name: string; role: Role }[];
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
