import { createClient } from './client'
import { useSessionStore } from '../stores/session'

let instance: ReturnType<typeof createClient> | null = null

/** Shared client; reads the current role from the session store on every request. */
export function useApi() {
  if (!instance) {
    const session = useSessionStore()
    instance = createClient({
      baseUrl: import.meta.env.VITE_API_BASE_URL,
      getRole: () => session.role,
    })
  }
  return instance
}

/** Test hook. */
export function setApi(c: ReturnType<typeof createClient> | null) {
  instance = c
}

export * from './client'
export * from './types'
