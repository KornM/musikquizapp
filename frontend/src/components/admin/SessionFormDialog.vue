<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="600"
  >
    <v-card>
      <v-card-title class="text-h5">Create New Quiz Session</v-card-title>

      <v-card-text>
        <error-alert v-if="error" :message="error" @close="error = null" />

        <v-form ref="formRef">
          <v-text-field
            v-model="title"
            label="Session Title"
            :rules="[rules.required]"
            variant="outlined"
            class="mb-3"
          />

          <v-textarea
            v-model="description"
            label="Description"
            :rules="[rules.required]"
            variant="outlined"
            rows="3"
          />
        </v-form>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="$emit('update:modelValue', false)">
          Cancel
        </v-btn>
        <v-btn color="primary" :loading="loading" @click="handleCreate">
          Create
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref } from "vue";
import { useSessionsStore } from "@/stores/sessions";
import ErrorAlert from "@/components/common/ErrorAlert.vue";

defineProps({
  modelValue: Boolean,
});

const emit = defineEmits(["update:modelValue", "created"]);

const sessionsStore = useSessionsStore();

const formRef = ref(null);
const title = ref("");
const description = ref("");
const loading = ref(false);
const error = ref(null);

const rules = {
  required: (value) => !!value || "This field is required",
};

const handleCreate = async () => {
  const { valid } = await formRef.value.validate();
  if (!valid) return;

  loading.value = true;
  error.value = null;

  const result = await sessionsStore.createSession({
    title: title.value,
    description: description.value,
  });

  loading.value = false;

  if (result.success) {
    title.value = "";
    description.value = "";
    emit("created");
  } else {
    error.value = result.error;
  }
};
</script>
