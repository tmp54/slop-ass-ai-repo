<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useSessionStore } from './stores/session'

const session = useSessionStore()
const router = useRouter()
function switchRole() {
  session.clear()
  void router.push('/')
}
</script>

<template>
  <a class="skip" href="#main">Skip to content</a>
  <header class="top">
    <div>
      <strong><RouterLink to="/handoffs">Developer Handoff Tool</RouterLink></strong>
      <span class="grow"></span>
      <template v-if="session.role">
        <span>Acting as <span class="badge" data-test="role-badge">{{ session.role }}</span></span>
        <button type="button" @click="switchRole">Switch role</button>
      </template>
    </div>
  </header>
  <main id="main" tabindex="-1"><RouterView /></main>
</template>
