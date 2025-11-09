<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="800"
    persistent
  >
    <v-card>
      <v-card-title class="text-h5">
        {{ editingRound ? "Edit Quiz Round" : "Add Quiz Round" }}
      </v-card-title>

      <v-card-text>
        <error-alert v-if="error" :message="error" @close="error = null" />

        <v-form ref="formRef">
          <v-text-field
            v-model="question"
            label="Question"
            :rules="[rules.required]"
            variant="outlined"
            placeholder="e.g., What is the name of this song?"
            class="mb-4"
          />

          <audio-upload
            v-model="audioFile"
            @uploaded="handleAudioUploaded"
            :session-id="sessionId"
          />

          <v-text-field
            v-for="(answer, index) in answers"
            :key="index"
            v-model="answers[index]"
            :label="`Answer ${String.fromCharCode(65 + index)}`"
            :rules="[rules.required]"
            variant="outlined"
            class="mb-2"
          />

          <v-radio-group
            v-model="correctAnswer"
            label="Correct Answer"
            :rules="[rules.required]"
          >
            <v-radio
              v-for="(answer, index) in answers"
              :key="index"
              :label="`${String.fromCharCode(65 + index)}: ${
                answer || '(empty)'
              }`"
              :value="index"
            />
          </v-radio-group>
        </v-form>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="handleCancel" :disabled="loading">
          Cancel
        </v-btn>
        <v-btn
          color="primary"
          :loading="loading"
          @click="handleSubmit"
          :disabled="!audioKey"
        >
          {{ editingRound ? "Save Changes" : "Add Round" }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch } from "vue";
import { useSessionsStore } from "@/stores/sessions";
import ErrorAlert from "@/components/common/ErrorAlert.vue";
import AudioUpload from "@/components/admin/AudioUpload.vue";

const props = defineProps({
  modelValue: Boolean,
  sessionId: {
    type: String,
    required: true,
  },
  editingRound: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(["update:modelValue", "created"]);

const sessionsStore = useSessionsStore();

const formRef = ref(null);
const question = ref("");
const audioFile = ref(null);
const audioKey = ref(null);
const answers = ref(["", "", "", ""]);
const correctAnswer = ref(null);
const loading = ref(false);
const error = ref(null);

const rules = {
  required: (value) =>
    (value !== null && value !== "") || "This field is required",
};

// Watch for editing round and populate form
watch(
  () => props.editingRound,
  (round) => {
    if (round) {
      question.value = round.question || "";
      answers.value = [...round.answers];
      correctAnswer.value = round.correctAnswer;
      audioKey.value = round.audioKey;
    } else {
      resetForm();
    }
  },
  { immediate: true }
);

const handleAudioUploaded = (key) => {
  audioKey.value = key;
};

const handleSubmit = async () => {
  const { valid } = await formRef.value.validate();
  if (!valid || !audioKey.value) return;

  loading.value = true;
  error.value = null;

  let result;
  if (props.editingRound) {
    // Update existing round
    result = await sessionsStore.updateRound(
      props.sessionId,
      props.editingRound.roundNumber,
      {
        question: question.value,
        audioKey: audioKey.value,
        answers: answers.value,
        correctAnswer: correctAnswer.value,
      }
    );
  } else {
    // Create new round
    result = await sessionsStore.addRound(props.sessionId, {
      question: question.value,
      audioKey: audioKey.value,
      answers: answers.value,
      correctAnswer: correctAnswer.value,
    });
  }

  loading.value = false;

  if (result.success) {
    resetForm();
    emit("created");
  } else {
    error.value = result.error;
  }
};

const handleCancel = () => {
  resetForm();
  emit("update:modelValue", false);
};

const resetForm = () => {
  question.value = "";
  audioFile.value = null;
  audioKey.value = null;
  answers.value = ["", "", "", ""];
  correctAnswer.value = null;
  error.value = null;
};
</script>
