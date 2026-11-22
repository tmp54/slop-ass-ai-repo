<script setup lang="ts">
import type { BriefVersion } from '../api/types'
import AiLabel from './AiLabel.vue'
import { fmtTime } from '../utils'

defineProps<{ brief: BriefVersion }>()
const unfetched = (g: string) => g.toLowerCase().startsWith('content not fetched')
</script>

<template>
  <section class="card" aria-labelledby="brief-h">
    <h2 id="brief-h">
      Handoff brief
      <AiLabel v-if="brief.source === 'ai'" />
      <span v-else class="badge">Edited by sender</span>
    </h2>
    <p class="meta">Version {{ brief.version }}, {{ fmtTime(brief.created_at) }}</p>
    <div :class="{ 'ai-box': brief.source === 'ai' }">
      <h3>Progress</h3>
      <p style="white-space:pre-wrap">{{ brief.content.progress }}</p>
      <template v-for="[title, items] in ([['Decisions', brief.content.decisions], ['Remaining tasks', brief.content.remaining_tasks], ['Blockers', brief.content.blockers]] as const)" :key="title">
        <h3>{{ title }}</h3>
        <ul v-if="items.length" class="plain"><li v-for="(x, i) in items" :key="i">{{ x }}</li></ul>
        <p v-else class="meta">None.</p>
      </template>
      <h3>References</h3>
      <ul v-if="brief.content.references.length" class="plain">
        <li v-for="r in brief.content.references" :key="r.url">
          <a :href="r.url" target="_blank" rel="noopener noreferrer">{{ r.title || r.url }}</a>
          <span v-if="r.note"> - {{ r.note }}</span>
        </li>
      </ul>
      <p v-else class="meta">None.</p>
    </div>
    <div class="gaps" data-test="gaps" style="margin-top:1rem">
      <h3 style="margin-top:0">Gaps flagged by the AI</h3>
      <ul v-if="brief.content.gaps.length" class="plain">
        <li v-for="(g, i) in brief.content.gaps" :key="i" :class="{ unfetched: unfetched(g) }">
          <span v-if="unfetched(g)">Link content could not be fetched. </span>{{ g }}
        </li>
      </ul>
      <p v-else class="meta" style="margin:0">No gaps flagged.</p>
    </div>
  </section>
</template>
