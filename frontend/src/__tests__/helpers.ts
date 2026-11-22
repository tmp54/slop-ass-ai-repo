import type { HandoffDetail, Status } from '../api/types'

export function detail(over: Partial<HandoffDetail> = {}): HandoffDetail {
  return {
    id: 1, title: 'T', notes: 'n', links: [], state: 'ai_drafted', question_count: 0,
    created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z',
    brief: {
      version: 1, source: 'ai', created_at: '2026-01-01T00:00:00Z',
      content: {
        progress: 'p', decisions: ['d1'], remaining_tasks: ['r1'], blockers: [],
        references: [{ url: 'https://github.com/a/b/pull/1', title: null, note: null }],
        gaps: ['content not fetched: https://github.com/a/b/pull/1', 'no tests described'],
      },
    },
    questions: [], restatements: [], confirmations: [], transitions: [],
    available_events: ['draft', 'approve', 'edit_brief'],
    ...over,
  }
}

export function status(over: Partial<Status> = {}): Status {
  return {
    id: 1, state: 'ai_drafted', updated_at: '2026-01-01T00:00:00Z', brief_version: 1,
    question_count: 0, unanswered_question_count: 0, restatement_count: 0,
    available_events: ['draft', 'approve', 'edit_brief'], ...over,
  }
}

export function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}
