<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useSessionStore } from '../stores/session'
import type { Role } from '../api/types'

const session = useSessionStore()
const router = useRouter()
function pick(r: Role) {
  session.setRole(r)
  void router.push('/handoffs')
}
</script>

<template>
  <section class="card">
    <h1>Who are you in this handoff?</h1>
    <p class="hint">There is no login in this prototype. Your choice decides which actions are offered.</p>
    <div class="row" role="group" aria-label="Choose your role">
      <button type="button" class="primary" data-test="pick-sender" @click="pick('sender')">I am the sender</button>
      <button type="button" class="primary" data-test="pick-receiver" @click="pick('receiver')">I am the receiver</button>
    </div>
  </section>
</template>
