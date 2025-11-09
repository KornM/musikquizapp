<template>
  <div class="loading-container">
    <v-progress-circular indeterminate color="primary" :size="size" />
    <p v-if="message" class="mt-4 text-body-1">{{ message }}</p>
  </div>
</template>

<script setup>
defineProps({
  message: {
    type: String,
    default: "",
  },
  size: {
    type: Number,
    default: 64,
  },
});
</script>

<style scoped>
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}
</style>
