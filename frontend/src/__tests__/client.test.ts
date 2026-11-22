import { describe, expect, it, vi } from 'vitest'
import { ApiError, createClient } from '../api/client'
import type { Role } from '../api/types'
import { detail, jsonResponse } from './helpers'

function setup(res: Response | Error, role: Role | null = 'sender') {
  const f = vi.fn(async () => { if (res instanceof Error) throw res; return res.clone() })
  const c = createClient({ baseUrl: 'http://x/', getRole: () => role, fetchImpl: f as unknown as typeof fetch })
  return { f, c }
}

describe('api client', () => {
  it('sends X-Role and JSON body to the right URL', async () => {
    const { f, c } = setup(jsonResponse(detail(), 201))
    await c.create({ title: 't', notes: 'n', links: ['https://a.b'] })
    const [url, init] = f.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe('http://x/handoffs')
    expect(init.method).toBe('POST')
    expect((init.headers as Record<string, string>)['X-Role']).toBe('sender')
    expect(init.body).toBe(JSON.stringify({ title: 't', notes: 'n', links: ['https://a.b'] }))
  })

  it('uses the current role on every request', async () => {
    let role: Role = 'sender'
    const f = vi.fn(async () => jsonResponse([]))
    const c = createClient({ getRole: () => role, fetchImpl: f as unknown as typeof fetch })
    await c.list()
    role = 'receiver'
    await c.list()
    const roles = f.mock.calls.map((x) => ((x as unknown as [string, RequestInit])[1].headers as Record<string, string>)['X-Role'])
    expect(roles).toEqual(['sender', 'receiver'])
  })

  it('maps endpoints to paths and bodies', async () => {
    const { f, c } = setup(jsonResponse({}))
    await c.requestRevision(3, 'fix')
    await c.confirm(3, null)
    await c.complete(3)
    await c.answer(3, 9, 'yes')
    await c.status(3)
    const calls = f.mock.calls.map((x) => { const [u, i] = x as unknown as [string, RequestInit]; return [i.method, u.replace('http://x', ''), i.body] })
    expect(calls).toEqual([
      ['POST', '/handoffs/3/request-revision', '{"comment":"fix"}'],
      ['POST', '/handoffs/3/confirm', '{"comment":null}'],
      ['POST', '/handoffs/3/complete', undefined],
      ['POST', '/handoffs/3/questions/9/answer', '{"answer":"yes"}'],
      ['GET', '/handoffs/3/status', undefined],
    ])
  })

  it('parses the contract error format into ApiError', async () => {
    const { c } = setup(jsonResponse({ error: { code: 'invalid_transition', message: 'wrong state', details: null } }, 409))
    const err = await c.approve(1).catch((e) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err).toMatchObject({ status: 409, code: 'invalid_transition', message: 'wrong state' })
  })

  it('keeps validation details', async () => {
    const { c } = setup(jsonResponse({ error: { code: 'validation_error', message: 'bad', details: [{ loc: ['body'] }] } }, 422))
    const err = (await c.create({ title: '', notes: '', links: [] }).catch((e) => e)) as ApiError
    expect(err.details).toEqual([{ loc: ['body'] }])
  })

  it('handles non-JSON errors and network failures', async () => {
    const a = await setup(new Response('boom', { status: 500 })).c.list().catch((e) => e)
    expect(a).toMatchObject({ status: 500, code: 'http_error' })
    const b = await setup(new TypeError('fail')).c.list().catch((e) => e)
    expect(b).toMatchObject({ status: 0, code: 'network_error' })
  })
})
