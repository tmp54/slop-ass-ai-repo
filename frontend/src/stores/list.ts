import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '../api'
import { describeError } from './handoff'
import type { HandoffSummary } from '../api/types'

export const useListStore = defineStore('list', () => {
  const items = ref<HandoffSummary[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  async function load() {
    loading.value = true
    error.value = null
    try {
      items.value = await useApi().list()
    } catch (e) {
      error.value = describeError(e)
    } finally {
      loading.value = false
    }
  }
  return { items, loading, error, load }
})
