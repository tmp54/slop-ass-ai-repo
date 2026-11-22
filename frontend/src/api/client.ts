import type {
  BriefContent,
  HandoffCreate,
  HandoffDetail,
  HandoffSummary,
  Question,
  Role,
  Status,
} from './types'

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details: unknown = null,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export interface ClientOptions {
  baseUrl?: string
  getRole: () => Role | null
  fetchImpl?: typeof fetch
}

/** Typed wrapper over the backend. Components must use this (via stores), never fetch. */
export function createClient(opts: ClientOptions) {
  const baseUrl = (opts.baseUrl ?? 'http://localhost:8000').replace(/\/$/, '')
  const doFetch = (...a: Parameters<typeof fetch>) => (opts.fetchImpl ?? fetch)(...a)

  async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const headers: Record<string, string> = {}
    const role = opts.getRole()
    if (role) headers['X-Role'] = role
    if (body !== undefined) headers['Content-Type'] = 'application/json'

    let res: Response
    try {
      res = await doFetch(baseUrl + path, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
      })
    } catch {
      throw new ApiError(0, 'network_error', 'Could not reach the backend. Is it running?')
    }

    if (!res.ok) {
      let code = 'http_error'
      let message = `Request failed (${res.status})`
      let details: unknown = null
      try {
        const data = await res.json()
        if (data?.error) {
          code = data.error.code ?? code
          message = data.error.message ?? message
          details = data.error.details ?? null
        }
      } catch {
        /* non-JSON error body */
      }
      throw new ApiError(res.status, code, message, details)
    }
    return (await res.json()) as T
  }

  const base = (id: number) => `/handoffs/${id}`
  return {
    health: () => request<{ status: string }>('GET', '/health'),
    list: () => request<HandoffSummary[]>('GET', '/handoffs'),
    create: (b: HandoffCreate) => request<HandoffDetail>('POST', '/handoffs', b),
    get: (id: number) => request<HandoffDetail>('GET', base(id)),
    status: (id: number) => request<Status>('GET', `${base(id)}/status`),
    draft: (id: number) => request<HandoffDetail>('POST', `${base(id)}/draft`),
    editBrief: (id: number, b: BriefContent) =>
      request<HandoffDetail>('PUT', `${base(id)}/brief`, b),
    approve: (id: number) => request<HandoffDetail>('POST', `${base(id)}/approve`),
    restate: (id: number, text: string) =>
      request<HandoffDetail>('POST', `${base(id)}/restatements`, { text }),
    requestRevision: (id: number, comment: string) =>
      request<HandoffDetail>('POST', `${base(id)}/request-revision`, { comment }),
    confirm: (id: number, comment: string | null) =>
      request<HandoffDetail>('POST', `${base(id)}/confirm`, { comment }),
    complete: (id: number) => request<HandoffDetail>('POST', `${base(id)}/complete`),
    ask: (id: number, text: string) =>
      request<Question>('POST', `${base(id)}/questions`, { text }),
    answer: (id: number, qid: number, answer: string) =>
      request<Question>('POST', `${base(id)}/questions/${qid}/answer`, { answer }),
  }
}

export type ApiClient = ReturnType<typeof createClient>
