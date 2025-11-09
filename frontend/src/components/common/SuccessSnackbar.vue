<template>
  <v-snackbar v-model="show" color="success" :timeout="timeout" location="top">
    {{ message }}
    <template #actions>
      <v-btn variant="text" @click="show = false"> Close </v-btn>
    </template>
  </v-snackbar>
</template>

<script setup>
import { ref, watch } from "vue";

const props = defineProps({
  message: {
    type: String,
    required: true,
  },
  modelValue: {
    type: Boolean,
    default: false,
  },
  timeout: {
    type: Number,
    default: 3000,
  },
});

const emit = defineEmits(["update:modelValue"]);

const show = ref(props.modelValue);

watch(
  () => props.modelValue,
  (val) => {
    show.value = val;
  }
);

watch(show, (val) => {
  emit("update:modelValue", val);
});
</script>
