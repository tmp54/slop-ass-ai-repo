// Hand-written from backend/docs/api-contract.md.
export type Role = 'sender' | 'receiver'
export type Actor = Role | 'ai'

export type HandoffState =
  | 'submitted'
  | 'ai_drafted'
  | 'sender_approved'
  | 'receiver_restated'
  | 'sender_confirmed'
  | 'completed'

export type HandoffEvent =
  | 'draft'
  | 'approve'
  | 'restate'
  | 'request_revision'
  | 'confirm'
  | 'complete'
  | 'edit_brief'
  | 'ask_question'
  | 'answer_question'

export interface HandoffCreate {
  title: string
  notes: string
  links: string[]
}

export interface Reference {
  url: string
  title: string | null
  note: string | null
}

export interface BriefContent {
  progress: string
  decisions: string[]
  remaining_tasks: string[]
  blockers: string[]
  references: Reference[]
  gaps: string[]
}

export interface BriefVersion {
  version: number
  source: 'ai' | 'sender'
  created_at: string
  content: BriefContent
}

export interface Question {
  id: number
  text: string
  answer: string | null
  created_at: string
  answered_at: string | null
}

export interface Restatement {
  id: number
  brief_version: number
  text: string
  misunderstandings: string[]
  created_at: string
}

export interface Confirmation {
  id: number
  restatement_id: number
  accepted: boolean
  comment: string | null
  created_at: string
}

export interface Transition {
  event: string
  from_state: string | null
  to_state: string
  actor: Actor
  created_at: string
}

export interface HandoffSummary {
  id: number
  title: string
  state: HandoffState
  question_count: number
  created_at: string
  updated_at: string
}

export interface HandoffDetail extends HandoffSummary {
  notes: string
  links: string[]
  brief: BriefVersion | null
  questions: Question[]
  restatements: Restatement[]
  confirmations: Confirmation[]
  transitions: Transition[]
  available_events: HandoffEvent[]
}

export interface Status {
  id: number
  state: HandoffState
  updated_at: string
  brief_version: number | null
  question_count: number
  unanswered_question_count: number
  restatement_count: number
  available_events: HandoffEvent[]
}

export interface ErrorBody {
  error: { code: string; message: string; details: unknown }
}
