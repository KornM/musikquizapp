<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="500"
  >
    <v-card>
      <v-card-title class="text-h5">Registration QR Code</v-card-title>

      <v-card-text class="text-center">
        <loading-spinner v-if="loading" message="Generating QR code..." />

        <div v-else-if="qrData">
          <qrcode-vue :value="qrData.registrationUrl" :size="300" level="H" />
          <p class="text-body-2 mt-4">{{ qrData.sessionTitle }}</p>
          <v-text-field
            :model-value="qrData.registrationUrl"
            readonly
            variant="outlined"
            class="mt-2"
          >
            <template #append>
              <v-btn icon="mdi-content-copy" variant="text" @click="copyUrl" />
            </template>
          </v-text-field>
        </div>

        <error-alert v-else-if="error" :message="error" />
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="$emit('update:modelValue', false)">
          Close
        </v-btn>
      </v-card-actions>
    </v-card>

    <success-snackbar
      v-model="showSuccess"
      message="URL copied to clipboard!"
    />
  </v-dialog>
</template>

<script setup>
import { ref, watch } from "vue";
import QrcodeVue from "qrcode.vue";
import api from "@/services/api";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import ErrorAlert from "@/components/common/ErrorAlert.vue";
import SuccessSnackbar from "@/components/common/SuccessSnackbar.vue";

const props = defineProps({
  modelValue: Boolean,
  sessionId: {
    type: String,
    required: true,
  },
});

defineEmits(["update:modelValue"]);

const loading = ref(false);
const error = ref(null);
const qrData = ref(null);
const showSuccess = ref(false);

watch(
  () => props.modelValue,
  async (val) => {
    if (val && !qrData.value) {
      await fetchQRData();
    }
  }
);

const fetchQRData = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await api.getQRData(props.sessionId);
    qrData.value = response.data;
  } catch (err) {
    error.value =
      err.response?.data?.error?.message || "Failed to generate QR code";
  } finally {
    loading.value = false;
  }
};

const copyUrl = async () => {
  try {
    await navigator.clipboard.writeText(qrData.value.registrationUrl);
    showSuccess.value = true;
  } catch (err) {
    console.error("Failed to copy:", err);
  }
};
</script>
