<script setup lang="ts">
import { ref } from 'vue'
import { useHandoffStore } from '../stores/handoff'
import AiLabel from './AiLabel.vue'
import { fmtTime } from '../utils'

const store = useHandoffStore()
const text = ref('')
const err = ref<string | null>(null)

async function submit() {
  if (!text.value.trim()) { err.value = 'Write your restatement of the next steps first.'; return }
  err.value = null
  if (await store.restate(text.value.trim())) text.value = ''
}
</script>

<template>
  <section class="card" aria-labelledby="r-h">
    <h2 id="r-h">Receiver restatements</h2>
    <p v-if="!store.detail?.restatements.length" class="meta">No restatement yet.</p>
    <article v-for="r in store.detail?.restatements" :key="r.id" style="margin-bottom:1rem" data-test="restatement">
      <p class="meta">Based on brief v{{ r.brief_version }}, {{ fmtTime(r.created_at) }}</p>
      <p style="white-space:pre-wrap">{{ r.text }}</p>
      <div class="ai-box">
        <p style="margin:0"><AiLabel /> Possible misunderstandings (may be inaccurate; the sender decides)</p>
        <ul v-if="r.misunderstandings.length" class="plain">
          <li v-for="(m, i) in r.misunderstandings" :key="i">{{ m }}</li>
        </ul>
        <p v-else class="meta" style="margin:0">None detected.</p>
      </div>
    </article>
    <form v-if="store.can('restate')" @submit.prevent="submit">
      <label for="restate">Restate the next steps in your own words</label>
      <textarea id="restate" v-model="text"></textarea>
      <p v-if="err" class="field-error" role="alert">{{ err }}</p>
      <div class="row"><button type="submit" class="primary" :disabled="store.busy" data-test="restate">Submit restatement</button></div>
    </form>
  </section>
</template>
