import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { ApiError, useApi } from '../api'
import type { BriefContent, HandoffDetail, HandoffEvent, Status } from '../api/types'

export const POLL_INTERVAL_MS = 5000

export function describeError(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.code === 'invalid_transition')
      return `That action is no longer allowed in the current state. The view has been refreshed. (${e.message})`
    if (e.code === 'ai_unavailable')
      return `The AI service is unavailable, nothing was changed. Please retry. (${e.message})`
    if (e.code === 'validation_error') return `Please check your input. (${e.message})`
    return e.message
  }
  return e instanceof Error ? e.message : 'Unexpected error'
}

export const useHandoffStore = defineStore('handoff', () => {
  const detail = ref<HandoffDetail | null>(null)
  const status = ref<Status | null>(null)
  const loading = ref(false)
  const busy = ref(false)
  const error = ref<ApiError | Error | null>(null)
  const pollError = ref<string | null>(null)
  let timer: ReturnType<typeof setInterval> | null = null
  let pollingId: number | null = null

  const errorMessage = computed(() => (error.value ? describeError(error.value) : null))
  const aiUnavailable = computed(
    () => error.value instanceof ApiError && error.value.code === 'ai_unavailable',
  )
  // Events come from the latest status (fresh) falling back to detail.
  const events = computed<HandoffEvent[]>(
    () => status.value?.available_events ?? detail.value?.available_events ?? [],
  )
  function can(ev: HandoffEvent) {
    return !busy.value && events.value.includes(ev)
  }

  function reset() {
    stopPolling()
    detail.value = null
    status.value = null
    error.value = null
    pollError.value = null
  }

  async function load(id: number) {
    loading.value = true
    error.value = null
    try {
      detail.value = await useApi().get(id)
    } catch (e) {
      error.value = e as Error
    } finally {
      loading.value = false
    }
  }

  function changed(prev: HandoffDetail | null, s: Status) {
    if (!prev) return true
    return (
      prev.state !== s.state ||
      (prev.brief?.version ?? null) !== s.brief_version ||
      prev.question_count !== s.question_count ||
      prev.updated_at !== s.updated_at
    )
  }

  async function poll(id: number) {
    try {
      const s = await useApi().status(id)
      if (pollingId !== id) return
      status.value = s
      pollError.value = null
      if (!busy.value && changed(detail.value, s)) {
        const d = await useApi().get(id)
        if (pollingId === id) detail.value = d
      }
    } catch (e) {
      pollError.value = describeError(e)
    }
  }

  function startPolling(id: number, intervalMs = POLL_INTERVAL_MS) {
    stopPolling()
    pollingId = id
    timer = setInterval(() => void poll(id), intervalMs)
  }
  function stopPolling() {
    if (timer) clearInterval(timer)
    timer = null
    pollingId = null
  }

  /** Run a mutating call; on success refresh state, on failure keep error and resync. */
  async function run<T>(fn: () => Promise<T>): Promise<T | undefined> {
    busy.value = true
    error.value = null
    try {
      const out = await fn()
      return out
    } catch (e) {
      error.value = e as Error
      if (e instanceof ApiError && (e.code === 'invalid_transition' || e.code === 'forbidden_role') && detail.value) {
        try { detail.value = await useApi().get(detail.value.id) } catch { /* keep old */ }
      }
      return undefined
    } finally {
      busy.value = false
    }
  }

  async function mutate(fn: (id: number) => Promise<HandoffDetail>): Promise<boolean> {
    const id = detail.value?.id
    if (id === undefined) return false
    const d = await run(() => fn(id))
    if (d) {
      detail.value = d
      status.value = null // stale; next poll refreshes
      return true
    }
    return false
  }

  async function create(title: string, notes: string, links: string[]): Promise<HandoffDetail | undefined> {
    const d = await run(() => useApi().create({ title, notes, links }))
    if (d) detail.value = d
    return d
  }

  const api = () => useApi()
  const redraft = () => mutate((id) => api().draft(id))
  const saveBrief = (b: BriefContent) => mutate((id) => api().editBrief(id, b))
  const approve = () => mutate((id) => api().approve(id))
  const restate = (text: string) => mutate((id) => api().restate(id, text))
  const requestRevision = (comment: string) => mutate((id) => api().requestRevision(id, comment))
  const confirm = (comment: string | null) => mutate((id) => api().confirm(id, comment))
  const complete = () => mutate((id) => api().complete(id))
  const ask = (text: string) =>
    mutate(async (id) => {
      await api().ask(id, text)
      return api().get(id)
    })
  const answer = (qid: number, text: string) =>
    mutate(async (id) => {
      await api().answer(id, qid, text)
      return api().get(id)
    })

  return {
    detail, status, loading, busy, error, errorMessage, aiUnavailable, pollError, events,
    can, reset, load, poll, startPolling, stopPolling, create,
    redraft, saveBrief, approve, restate, requestRevision, confirm, complete, ask, answer,
  }
})
