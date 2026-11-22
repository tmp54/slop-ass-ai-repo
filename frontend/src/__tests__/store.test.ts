import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ApiError, setApi } from '../api'
import { useHandoffStore, describeError } from '../stores/handoff'
import { detail, status } from './helpers'

function mockApi(over: Record<string, unknown> = {}) {
  const api = {
    get: vi.fn(async () => detail()),
    status: vi.fn(async () => status()),
    draft: vi.fn(async () => detail()),
    approve: vi.fn(async () => detail({ state: 'sender_approved', available_events: [] })),
    ask: vi.fn(async () => ({})),
    ...over,
  }
  setApi(api as never)
  return api
}

beforeEach(() => { setActivePinia(createPinia()); vi.useFakeTimers() })
afterEach(() => { vi.useRealTimers(); setApi(null) })

describe('handoff store', () => {
  it('only reports events the backend offers', async () => {
    mockApi()
    const s = useHandoffStore()
    await s.load(1)
    expect(s.can('approve')).toBe(true)
    expect(s.can('complete')).toBe(false)
  })

  it('status events override detail events', async () => {
    const api = mockApi({ status: vi.fn(async () => status({ available_events: [] })) })
    const s = useHandoffStore()
    await s.load(1)
    await s.poll(1) // pollingId not set -> ignored
    s.startPolling(1, 1000)
    await vi.advanceTimersByTimeAsync(1000)
    expect(api.status).toHaveBeenCalled()
    expect(s.can('approve')).toBe(false)
    s.stopPolling()
  })

  it('polling refetches detail only when something changed', async () => {
    const api = mockApi()
    const s = useHandoffStore()
    await s.load(1)
    s.startPolling(1, 1000)
    await vi.advanceTimersByTimeAsync(1000)
    expect(api.get).toHaveBeenCalledTimes(1) // unchanged
    api.status.mockResolvedValue(status({ state: 'sender_approved', updated_at: '2026-01-02T00:00:00Z' }))
    api.get.mockResolvedValue(detail({ state: 'sender_approved' }))
    await vi.advanceTimersByTimeAsync(1000)
    expect(api.get).toHaveBeenCalledTimes(2)
    expect(s.detail?.state).toBe('sender_approved')
    s.stopPolling()
  })

  it('stops polling on stopPolling', async () => {
    const api = mockApi()
    const s = useHandoffStore()
    s.startPolling(1, 1000)
    s.stopPolling()
    await vi.advanceTimersByTimeAsync(5000)
    expect(api.status).not.toHaveBeenCalled()
  })

  it('on 409 invalid_transition sets error and resyncs detail', async () => {
    const api = mockApi({
      approve: vi.fn(async () => { throw new ApiError(409, 'invalid_transition', 'wrong state') }),
    })
    const s = useHandoffStore()
    await s.load(1)
    api.get.mockResolvedValue(detail({ state: 'sender_approved', available_events: [] }))
    expect(await s.approve()).toBe(false)
    expect(s.errorMessage).toMatch(/no longer allowed/)
    expect(s.detail?.state).toBe('sender_approved')
    expect(s.busy).toBe(false)
  })

  it('on 502 ai_unavailable flags retry and retry succeeds', async () => {
    const draft = vi.fn()
      .mockRejectedValueOnce(new ApiError(502, 'ai_unavailable', 'down'))
      .mockResolvedValueOnce(detail({ state: 'ai_drafted' }))
    mockApi({ draft })
    const s = useHandoffStore()
    await s.load(1)
    expect(await s.redraft()).toBe(false)
    expect(s.aiUnavailable).toBe(true)
    expect(await s.redraft()).toBe(true)
    expect(s.aiUnavailable).toBe(false)
    expect(s.error).toBeNull()
  })

  it('ask refetches detail', async () => {
    const api = mockApi()
    const s = useHandoffStore()
    await s.load(1)
    await s.ask('why?')
    expect(api.ask).toHaveBeenCalledWith(1, 'why?')
    expect(api.get).toHaveBeenCalledTimes(2)
  })

  it('describeError handles unknown errors', () => {
    expect(describeError(new Error('x'))).toBe('x')
    expect(describeError('?')).toBe('Unexpected error')
  })
})
