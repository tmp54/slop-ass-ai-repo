<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useHandoffStore } from '../stores/handoff'
import { isHttpUrl, parseLinks } from '../utils'
import ErrorAlert from '../components/ErrorAlert.vue'

const store = useHandoffStore()
const router = useRouter()
const title = ref('')
const notes = ref('')
const linksText = ref('')
const submitted = ref(false)

const links = computed(() => parseLinks(linksText.value))
const errors = computed(() => {
  const e: Record<string, string> = {}
  if (!title.value.trim()) e.title = 'Title is required.'
  else if (title.value.length > 200) e.title = 'Title must be at most 200 characters.'
  if (!notes.value.trim()) e.notes = 'Notes are required.'
  else if (notes.value.length > 20000) e.notes = 'Notes must be at most 20000 characters.'
  const bad = links.value.filter((l) => !isHttpUrl(l))
  if (bad.length) e.links = `Not valid http(s) URLs: ${bad.join(', ')}`
  else if (links.value.length > 20) e.links = 'At most 20 links.'
  return e
})

async function submit() {
  submitted.value = true
  if (Object.keys(errors.value).length) return
  store.error = null
  const d = await store.create(title.value.trim(), notes.value.trim(), links.value)
  if (d) await router.push(`/handoffs/${d.id}`)
}
</script>

<template>
  <h1>New handoff</h1>
  <form class="card" novalidate @submit.prevent="submit">
    <label for="title">Title</label>
    <input id="title" v-model="title" type="text" maxlength="200" :aria-invalid="submitted && !!errors.title" aria-describedby="title-e" />
    <p id="title-e" class="field-error">{{ submitted ? errors.title : '' }}</p>

    <label for="notes">Notes <span class="hint">(progress, decisions, what is left, blockers)</span></label>
    <textarea id="notes" v-model="notes" rows="10" :aria-invalid="submitted && !!errors.notes" aria-describedby="notes-e"></textarea>
    <p id="notes-e" class="field-error">{{ submitted ? errors.notes : '' }}</p>

    <label for="links">GitHub PR / issue links <span class="hint">(one per line or comma separated, optional)</span></label>
    <textarea id="links" v-model="linksText" :aria-invalid="submitted && !!errors.links" aria-describedby="links-e"></textarea>
    <p id="links-e" class="field-error">{{ submitted ? errors.links : '' }}</p>

    <p class="hint">The AI will draft a structured brief from this. Text and links only; file upload is not supported.</p>
    <ErrorAlert :message="store.errorMessage" />
    <div class="row">
      <button type="submit" class="primary" :disabled="store.busy" data-test="submit">
        {{ store.busy ? 'Submitting and drafting...' : 'Submit and draft brief' }}
      </button>
    </div>
  </form>
</template>
