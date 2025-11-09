<template>
  <v-alert
    v-if="show"
    type="error"
    closable
    @click:close="handleClose"
    class="mb-4"
  >
    {{ message }}
  </v-alert>
</template>

<script setup>
import { ref, watch } from "vue";

const props = defineProps({
  message: {
    type: String,
    required: true,
  },
  autoDismiss: {
    type: Boolean,
    default: false,
  },
  timeout: {
    type: Number,
    default: 5000,
  },
});

const emit = defineEmits(["close"]);

const show = ref(true);

watch(
  () => props.message,
  () => {
    show.value = true;
    if (props.autoDismiss) {
      setTimeout(() => {
        show.value = false;
        emit("close");
      }, props.timeout);
    }
  }
);

const handleClose = () => {
  show.value = false;
  emit("close");
};
</script>
