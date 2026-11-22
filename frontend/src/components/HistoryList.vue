<script setup lang="ts">
import type { Transition } from '../api/types'
import { fmtTime } from '../utils'
defineProps<{ transitions: Transition[] }>()
</script>

<template>
  <section class="card" aria-labelledby="hist-h">
    <h2 id="hist-h">History</h2>
    <ol class="plain">
      <li v-for="(t, i) in transitions" :key="i">
        {{ t.event }} by {{ t.actor }} ({{ t.from_state ?? 'start' }} to {{ t.to_state }})
        <span class="meta">{{ fmtTime(t.created_at) }}</span>
      </li>
    </ol>
  </section>
</template>
