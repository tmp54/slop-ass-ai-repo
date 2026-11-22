import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Role } from '../api/types'

const KEY = 'handoff.role'

function load(): Role | null {
  try {
    const v = localStorage.getItem(KEY)
    return v === 'sender' || v === 'receiver' ? v : null
  } catch {
    return null
  }
}

export const useSessionStore = defineStore('session', () => {
  const role = ref<Role | null>(load())
  function setRole(r: Role) {
    role.value = r
    try { localStorage.setItem(KEY, r) } catch { /* ignore */ }
  }
  function clear() {
    role.value = null
    try { localStorage.removeItem(KEY) } catch { /* ignore */ }
  }
  return { role, setRole, clear }
})
