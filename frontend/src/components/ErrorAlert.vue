<script setup lang="ts">
defineProps<{ message: string | null }>()
</script>

<template>
  <div v-if="message" class="alert error" role="alert" data-test="error">
    <p style="margin:0">{{ message }}</p>
    <slot />
  </div>
</template>
