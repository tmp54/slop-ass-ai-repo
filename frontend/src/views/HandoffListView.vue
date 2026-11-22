<script setup lang="ts">
import { onMounted } from 'vue'
import { useListStore } from '../stores/list'
import { useSessionStore } from '../stores/session'
import { STATE_LABEL, fmtTime } from '../utils'
import ErrorAlert from '../components/ErrorAlert.vue'

const list = useListStore()
const session = useSessionStore()
onMounted(() => list.load())
</script>

<template>
  <h1>Handoffs</h1>
  <div class="row" style="margin-bottom:1rem">
    <RouterLink v-if="session.role === 'sender'" to="/handoffs/new" data-test="new-link">Create a new handoff</RouterLink>
    <button type="button" :disabled="list.loading" @click="list.load()">Refresh</button>
  </div>
  <ErrorAlert :message="list.error"><button type="button" @click="list.load()">Retry</button></ErrorAlert>
  <p v-if="list.loading" role="status">Loading...</p>
  <p v-else-if="!list.items.length && !list.error" class="meta">No handoffs yet.</p>
  <ul style="list-style:none;padding:0">
    <li v-for="h in list.items" :key="h.id" class="card">
      <RouterLink :to="`/handoffs/${h.id}`"><strong>{{ h.title }}</strong></RouterLink>
      <span class="badge" style="margin-left:.5rem">{{ STATE_LABEL[h.state] }}</span>
      <div class="meta">{{ h.question_count }} question(s), updated {{ fmtTime(h.updated_at) }}</div>
    </li>
  </ul>
</template>
