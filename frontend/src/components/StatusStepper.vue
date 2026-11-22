<script setup lang="ts">
import { computed } from 'vue'
import type { HandoffState } from '../api/types'
import { STATE_LABEL, STATE_ORDER, STATE_WAITING } from '../utils'

const props = defineProps<{ state: HandoffState; pollError?: string | null }>()
const idx = computed(() => STATE_ORDER.indexOf(props.state))
</script>

<template>
  <section class="card" aria-labelledby="status-h">
    <h2 id="status-h">Status: <span class="badge" data-test="state">{{ STATE_LABEL[state] }}</span></h2>
    <p aria-live="polite" data-test="waiting">{{ STATE_WAITING[state] }}</p>
    <ol class="steps" aria-label="Progress">
      <li v-for="(s, i) in STATE_ORDER" :key="s" :class="{ done: i < idx, current: i === idx }"
          :aria-current="i === idx ? 'step' : undefined">
        {{ STATE_LABEL[s] }}
      </li>
    </ol>
    <p v-if="pollError" class="meta" role="status">Live updates paused: {{ pollError }} Retrying.</p>
  </section>
</template>
