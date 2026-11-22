<script setup lang="ts">
import { ref } from 'vue'
import { useHandoffStore } from '../stores/handoff'

const store = useHandoffStore()
const revision = ref('')
const confirmComment = ref('')
const revErr = ref<string | null>(null)

async function requestRevision() {
  if (!revision.value.trim()) { revErr.value = 'Explain what the receiver should correct.'; return }
  revErr.value = null
  if (await store.requestRevision(revision.value.trim())) revision.value = ''
}
async function confirm() {
  if (await store.confirm(confirmComment.value.trim() || null)) confirmComment.value = ''
}
</script>

<template>
  <section v-if="store.can('request_revision') || store.can('confirm') || store.can('complete')" class="card" aria-labelledby="sa-h">
    <h2 id="sa-h">Your decision</h2>
    <template v-if="store.events.includes('request_revision') || store.events.includes('confirm')">
      <p>Review the receiver's restatement above. Confirm it if it is correct, or request a revision.</p>
      <label for="conf-c">Confirmation comment <span class="hint">(optional)</span></label>
      <textarea id="conf-c" v-model="confirmComment"></textarea>
      <div class="row">
        <button type="button" class="primary" :disabled="!store.can('confirm')" data-test="confirm" @click="confirm">Confirm restatement</button>
      </div>
      <label for="rev-c">Revision request <span class="hint">(required)</span></label>
      <textarea id="rev-c" v-model="revision"></textarea>
      <p v-if="revErr" class="field-error" role="alert">{{ revErr }}</p>
      <div class="row">
        <button type="button" class="danger" :disabled="!store.can('request_revision')" data-test="revise" @click="requestRevision">Request revision</button>
      </div>
    </template>
    <template v-if="store.events.includes('complete')">
      <p>The restatement is confirmed. Completing is a separate final step.</p>
      <div class="row">
        <button type="button" class="primary" :disabled="!store.can('complete')" data-test="complete" @click="store.complete()">Complete handoff</button>
      </div>
    </template>
  </section>
</template>
