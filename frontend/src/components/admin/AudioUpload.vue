<template>
  <div class="audio-upload mb-4">
    <v-card
      :class="['drop-zone', { 'drag-over': isDragging }]"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
      @click="$refs.fileInput.click()"
    >
      <v-card-text class="text-center">
        <v-icon size="64" color="primary">mdi-cloud-upload</v-icon>
        <p class="text-h6 mt-2">
          {{ file ? file.name : "Drop audio file here or click to browse" }}
        </p>
        <p class="text-caption">Supported formats: MP3, WAV, OGG (max 10MB)</p>

        <v-progress-linear
          v-if="uploading"
          indeterminate
          color="primary"
          class="mt-4"
        />

        <v-alert v-if="uploadError" type="error" class="mt-4">
          {{ uploadError }}
        </v-alert>

        <v-alert v-if="uploadSuccess" type="success" class="mt-4">
          Audio uploaded successfully!
        </v-alert>
      </v-card-text>
    </v-card>

    <input
      ref="fileInput"
      type="file"
      accept="audio/*"
      style="display: none"
      @change="handleFileSelect"
    />

    <audio
      v-if="file && audioUrl"
      :src="audioUrl"
      controls
      class="mt-4"
      style="width: 100%"
    />
  </div>
</template>

<script setup>
import { ref, watch } from "vue";
import { useSessionsStore } from "@/stores/sessions";

const props = defineProps({
  modelValue: File,
  sessionId: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(["update:modelValue", "uploaded"]);

const sessionsStore = useSessionsStore();

const fileInput = ref(null);
const file = ref(null);
const audioUrl = ref(null);
const isDragging = ref(false);
const uploading = ref(false);
const uploadError = ref(null);
const uploadSuccess = ref(false);

watch(
  () => props.modelValue,
  (val) => {
    file.value = val;
  }
);

const validateFile = (selectedFile) => {
  const maxSize = 10 * 1024 * 1024; // 10MB
  const validTypes = ["audio/mpeg", "audio/wav", "audio/ogg", "audio/mp3"];

  if (selectedFile.size > maxSize) {
    uploadError.value = "File size must be less than 10MB";
    return false;
  }

  if (
    !validTypes.includes(selectedFile.type) &&
    !selectedFile.name.match(/\.(mp3|wav|ogg)$/i)
  ) {
    uploadError.value = "Invalid file type. Please upload MP3, WAV, or OGG";
    return false;
  }

  return true;
};

const handleFileSelect = (event) => {
  const selectedFile = event.target.files[0];
  if (selectedFile) {
    processFile(selectedFile);
  }
};

const handleDrop = (event) => {
  isDragging.value = false;
  const selectedFile = event.dataTransfer.files[0];
  if (selectedFile) {
    processFile(selectedFile);
  }
};

const processFile = async (selectedFile) => {
  uploadError.value = null;
  uploadSuccess.value = false;

  if (!validateFile(selectedFile)) {
    return;
  }

  file.value = selectedFile;
  emit("update:modelValue", selectedFile);

  // Create preview URL
  audioUrl.value = URL.createObjectURL(selectedFile);

  // Upload file
  uploading.value = true;
  const result = await sessionsStore.uploadAudio(selectedFile, props.sessionId);
  uploading.value = false;

  if (result.success) {
    uploadSuccess.value = true;
    emit("uploaded", result.data.audioKey);
  } else {
    uploadError.value = result.error;
  }
};
</script>

<style scoped>
.drop-zone {
  cursor: pointer;
  transition: all 0.3s;
  border: 2px dashed #ccc;
}

.drop-zone:hover,
.drop-zone.drag-over {
  border-color: #1976d2;
  background-color: rgba(25, 118, 210, 0.05);
}
</style>
