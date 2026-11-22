import type { HandoffState } from './api/types'

export const linesToArray = (s: string): string[] =>
  s.split('\n').map((l) => l.trim()).filter(Boolean)
export const arrayToLines = (a: string[]): string => a.join('\n')

export const STATE_ORDER: HandoffState[] = [
  'submitted', 'ai_drafted', 'sender_approved', 'receiver_restated', 'sender_confirmed', 'completed',
]

export const STATE_LABEL: Record<HandoffState, string> = {
  submitted: 'Submitted',
  ai_drafted: 'AI drafted',
  sender_approved: 'Sender approved',
  receiver_restated: 'Receiver restated',
  sender_confirmed: 'Sender confirmed',
  completed: 'Completed',
}

/** Who needs to act next, for the status view. */
export const STATE_WAITING: Record<HandoffState, string> = {
  submitted: 'Waiting for the AI draft (sender can retry).',
  ai_drafted: 'Waiting for the sender to review and approve the AI draft.',
  sender_approved: 'Waiting for the receiver to read the brief and write a restatement.',
  receiver_restated: 'Waiting for the sender to confirm the restatement or request a revision.',
  sender_confirmed: 'Waiting for the sender to complete the handoff.',
  completed: 'Handoff complete. The brief is final.',
}

export function parseLinks(s: string): string[] {
  return s.split(/[\s,]+/).map((x) => x.trim()).filter(Boolean)
}

export function isHttpUrl(s: string): boolean {
  try {
    const u = new URL(s)
    return u.protocol === 'http:' || u.protocol === 'https:'
  } catch {
    return false
  }
}

export const fmtTime = (iso: string) => new Date(iso).toLocaleString()
