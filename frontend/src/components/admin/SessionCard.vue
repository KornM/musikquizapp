<template>
  <div>
    <v-card elevation="2" hover>
      <v-card-title class="d-flex align-center">
        <span class="text-truncate">{{ session.title }}</span>
        <v-spacer />
        <v-chip :color="statusColor" size="small" variant="flat">
          {{ session.status }}
        </v-chip>
      </v-card-title>

      <v-card-text>
        <p class="text-body-2 mb-2">{{ session.description }}</p>
        <v-chip size="small" class="mr-2">
          <v-icon start>mdi-music-circle</v-icon>
          {{ session.roundCount }} rounds
        </v-chip>
      </v-card-text>

      <v-card-actions>
        <v-btn variant="text" color="primary" @click="viewDetails">
          View Details
        </v-btn>
        <v-btn variant="text" color="secondary" @click="showPresentation">
          Present
        </v-btn>
        <v-btn variant="text" color="accent" @click="showQR"> QR Code </v-btn>
        <v-spacer />
        <v-btn
          variant="text"
          color="error"
          icon="mdi-delete"
          @click="confirmDelete"
        />
      </v-card-actions>
    </v-card>

    <QRCodeModal v-model="qrDialog" :session-id="session.sessionId" />

    <v-dialog v-model="deleteDialog" max-width="500">
      <v-card>
        <v-card-title>Delete Session?</v-card-title>
        <v-card-text>
          <p class="mb-2">
            Are you sure you want to delete
            <strong>"{{ session.title }}"</strong>?
          </p>
          <p class="text-error">This will permanently delete:</p>
          <ul class="ml-4">
            <li>The quiz session</li>
            <li>All {{ session.roundCount }} rounds</li>
            <li>All audio files from S3</li>
          </ul>
          <p class="mt-2"><strong>This action cannot be undone.</strong></p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">Cancel</v-btn>
          <v-btn color="error" @click="handleDelete" :loading="deleting"
            >Delete</v-btn
          >
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import QRCodeModal from "./QRCodeModal.vue";

const props = defineProps({
  session: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["deleted"]);

const router = useRouter();
const qrDialog = ref(false);
const deleteDialog = ref(false);
const deleting = ref(false);

const statusColor = computed(() => {
  switch (props.session.status) {
    case "active":
      return "success";
    case "draft":
      return "warning";
    case "completed":
      return "info";
    default:
      return "grey";
  }
});

const viewDetails = () => {
  router.push(`/admin/sessions/${props.session.sessionId}`);
};

const showPresentation = () => {
  router.push(`/admin/sessions/${props.session.sessionId}/present`);
};

const showQR = () => {
  qrDialog.value = true;
};

const confirmDelete = () => {
  deleteDialog.value = true;
};

const handleDelete = async () => {
  deleting.value = true;
  emit("deleted", props.session.sessionId);
  deleteDialog.value = false;
  deleting.value = false;
};
</script>
