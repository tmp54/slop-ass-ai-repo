<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useHandoffStore } from '../stores/handoff'
import { fmtTime } from '../utils'

const store = useHandoffStore()
const text = ref('')
const askError = ref<string | null>(null)
const answers = reactive<Record<number, string>>({})
const answerErrors = reactive<Record<number, string>>({})

async function ask() {
  if (!text.value.trim()) { askError.value = 'Enter a question.'; return }
  askError.value = null
  if (await store.ask(text.value.trim())) text.value = ''
}
async function answer(id: number) {
  if (!answers[id]?.trim()) { answerErrors[id] = 'Enter an answer.'; return }
  delete answerErrors[id]
  if (await store.answer(id, answers[id].trim())) delete answers[id]
}
</script>

<template>
  <section class="card" aria-labelledby="q-h">
    <h2 id="q-h">Questions ({{ store.detail?.questions.length ?? 0 }})</h2>
    <p v-if="!store.detail?.questions.length" class="meta">No questions yet.</p>
    <ul class="plain" style="list-style:none;padding:0">
      <li v-for="q in store.detail?.questions" :key="q.id" style="margin-bottom:1rem" data-test="question">
        <strong>Q:</strong> {{ q.text }} <span class="meta">({{ fmtTime(q.created_at) }})</span>
        <div v-if="q.answer"><strong>A:</strong> {{ q.answer }}</div>
        <div v-else-if="store.can('answer_question')">
          <label :for="`ans-${q.id}`">Your answer</label>
          <textarea :id="`ans-${q.id}`" v-model="answers[q.id]"></textarea>
          <p v-if="answerErrors[q.id]" class="field-error" role="alert">{{ answerErrors[q.id] }}</p>
          <div class="row"><button type="button" class="primary" :disabled="store.busy" @click="answer(q.id)">Send answer</button></div>
        </div>
        <div v-else class="meta">Unanswered.</div>
      </li>
    </ul>
    <form v-if="store.can('ask_question')" @submit.prevent="ask">
      <label for="q-new">Ask the sender a question</label>
      <textarea id="q-new" v-model="text"></textarea>
      <p v-if="askError" class="field-error" role="alert">{{ askError }}</p>
      <div class="row"><button type="submit" class="primary" :disabled="store.busy" data-test="ask">Ask question</button></div>
    </form>
  </section>
</template>
