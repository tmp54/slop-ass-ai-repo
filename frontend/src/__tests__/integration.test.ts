// Opt-in: VITE_TEST_BACKEND_URL=http://localhost:8000 npm test
import { describe, expect, it } from 'vitest'
import { createClient } from '../api/client'

const url = import.meta.env.VITE_TEST_BACKEND_URL as string | undefined
describe.skipIf(!url)('live backend happy path', () => {
  it('runs the whole workflow', async () => {
    let role: 'sender' | 'receiver' = 'sender'
    const c = createClient({ baseUrl: url, getRole: () => role })
    const h = await c.create({ title: 'it', notes: 'notes', links: ['https://github.com/a/b/pull/1'] })
    expect(h.state).toBe('ai_drafted')
    expect((await c.approve(h.id)).state).toBe('sender_approved')
    role = 'receiver'
    expect((await c.get(h.id)).brief).not.toBeNull()
    expect((await c.restate(h.id, 'I will do X')).state).toBe('receiver_restated')
    await c.ask(h.id, 'q?').catch(() => undefined)
    role = 'sender'
    expect((await c.confirm(h.id, null)).state).toBe('sender_confirmed')
    expect((await c.complete(h.id)).state).toBe('completed')
    await expect(c.approve(h.id)).rejects.toMatchObject({ status: 409, code: 'invalid_transition' })
  })
})
