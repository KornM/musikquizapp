<template>
  <div>
    <v-card elevation="8" hover class="session-card">
      <div class="card-header" :class="headerClass">
        <v-icon size="40" color="white" class="header-icon">{{
          mediaIcon
        }}</v-icon>
      </div>

      <v-card-title class="d-flex align-center pt-4">
        <span class="text-truncate font-weight-bold">{{ session.title }}</span>
        <v-spacer />
        <v-chip :color="statusColor" size="small" variant="flat">
          {{ session.status }}
        </v-chip>
      </v-card-title>

      <v-card-text>
        <p class="text-body-2 mb-3">{{ session.description }}</p>
        <div class="d-flex align-center mb-3">
          <v-chip size="small" color="primary" variant="tonal" class="mr-2">
            <v-icon start size="small">mdi-music-circle</v-icon>
            {{ session.roundCount }} rounds
          </v-chip>
          <v-chip size="small" color="secondary" variant="tonal">
            <v-icon start size="small">{{ mediaTypeIcon }}</v-icon>
            {{ mediaTypeLabel }}
          </v-chip>
        </div>

        <!-- Mini Scoreboard -->
        <div v-if="scoreboard && scoreboard.length > 0" class="mini-scoreboard">
          <div class="d-flex align-center mb-2">
            <v-icon size="small" class="mr-1">mdi-trophy</v-icon>
            <span class="text-caption font-weight-bold">Top Players</span>
            <v-spacer />
            <v-btn
              icon
              size="x-small"
              variant="text"
              @click.stop="refreshScoreboard"
              :loading="loadingScoreboard"
            >
              <v-icon size="small">mdi-refresh</v-icon>
            </v-btn>
          </div>
          <div
            v-for="(participant, index) in scoreboard.slice(0, 3)"
            :key="participant.participantId"
            class="mini-scoreboard-item"
          >
            <span class="rank-badge" :class="getRankClass(index)">{{
              index + 1
            }}</span>
            <span class="participant-avatar">{{ participant.avatar }}</span>
            <span class="participant-name text-truncate">{{
              participant.name
            }}</span>
            <v-spacer />
            <span class="participant-points">{{
              participant.totalPoints
            }}</span>
          </div>
        </div>
        <div v-else-if="loadingScoreboard" class="text-center py-2">
          <v-progress-circular
            indeterminate
            size="20"
            width="2"
          ></v-progress-circular>
        </div>
        <div v-else class="text-caption text-grey text-center py-2">
          No participants yet
        </div>
      </v-card-text>

      <v-card-actions>
        <v-btn
          variant="tonal"
          color="primary"
          prepend-icon="mdi-eye"
          @click="viewDetails"
        >
          Details
        </v-btn>
        <v-btn
          variant="tonal"
          color="secondary"
          prepend-icon="mdi-presentation"
          @click="showPresentation"
        >
          Present
        </v-btn>
        <v-btn
          v-if="session.status === 'active'"
          variant="tonal"
          color="success"
          prepend-icon="mdi-check-circle"
          @click="confirmComplete"
        >
          Complete
        </v-btn>
        <v-btn
          variant="text"
          color="accent"
          icon="mdi-qrcode"
          @click="showQR"
        />
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

    <v-dialog v-model="completeDialog" max-width="500">
      <v-card>
        <v-card-title>Complete Session?</v-card-title>
        <v-card-text>
          <p class="mb-2">
            Are you sure you want to mark
            <strong>"{{ session.title }}"</strong> as completed?
          </p>
          <p class="text-warning">This will:</p>
          <ul class="ml-4">
            <li>Prevent participants from submitting new answers</li>
            <li>Redirect participants back to the lobby</li>
            <li>Mark the session as inactive</li>
          </ul>
          <p class="mt-2">You can still view results and the scoreboard.</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="completeDialog = false">Cancel</v-btn>
          <v-btn color="success" @click="handleComplete" :loading="completing"
            >Complete Session</v-btn
          >
        </v-card-actions>
      </v-card>
    </v-dialog>

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
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import api from "@/services/api";
import QRCodeModal from "./QRCodeModal.vue";

const props = defineProps({
  session: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["deleted", "completed"]);

const router = useRouter();
const qrDialog = ref(false);
const deleteDialog = ref(false);
const completeDialog = ref(false);
const deleting = ref(false);
const completing = ref(false);
const scoreboard = ref([]);
const loadingScoreboard = ref(false);

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

const mediaTypeIcon = computed(() => {
  const mediaType = props.session.mediaType || "audio";
  switch (mediaType) {
    case "audio":
      return "mdi-music";
    case "image":
      return "mdi-image";
    case "none":
      return "mdi-text";
    default:
      return "mdi-music";
  }
});

const mediaTypeLabel = computed(() => {
  const mediaType = props.session.mediaType || "audio";
  switch (mediaType) {
    case "audio":
      return "Music";
    case "image":
      return "Pictures";
    case "none":
      return "Text Only";
    default:
      return "Music";
  }
});

const mediaIcon = computed(() => {
  const mediaType = props.session.mediaType || "audio";
  switch (mediaType) {
    case "audio":
      return "mdi-music-note";
    case "image":
      return "mdi-image-multiple";
    case "none":
      return "mdi-text-box";
    default:
      return "mdi-music-note";
  }
});

const headerClass = computed(() => {
  const mediaType = props.session.mediaType || "audio";
  switch (mediaType) {
    case "audio":
      return "header-music";
    case "image":
      return "header-image";
    case "none":
      return "header-text";
    default:
      return "header-music";
  }
});

onMounted(() => {
  refreshScoreboard();
});

const refreshScoreboard = async () => {
  loadingScoreboard.value = true;
  try {
    const response = await api.getScoreboard(props.session.sessionId);
    scoreboard.value = response.data.scoreboard || [];
  } catch (err) {
    console.error("Failed to load scoreboard:", err);
    scoreboard.value = [];
  } finally {
    loadingScoreboard.value = false;
  }
};

const getRankClass = (index) => {
  if (index === 0) return "rank-gold";
  if (index === 1) return "rank-silver";
  if (index === 2) return "rank-bronze";
  return "";
};

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

const confirmComplete = () => {
  completeDialog.value = true;
};

const handleComplete = async () => {
  completing.value = true;
  try {
    await api.completeSession(props.session.sessionId);
    completeDialog.value = false;
    // Emit event to refresh session list
    emit("completed", props.session.sessionId);
  } catch (err) {
    console.error("Failed to complete session:", err);
  } finally {
    completing.value = false;
  }
};

const handleDelete = async () => {
  deleting.value = true;
  emit("deleted", props.session.sessionId);
  deleteDialog.value = false;
  deleting.value = false;
};
</script>

<style scoped>
.session-card {
  border-radius: 12px !important;
  transition: transform 0.2s, box-shadow 0.2s;
  overflow: hidden;
}

.session-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15) !important;
}

.card-header {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.header-music {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.header-image {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.header-text {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.header-icon {
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
}

.mini-scoreboard {
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  padding: 8px;
}

.mini-scoreboard-item {
  display: flex;
  align-items: center;
  padding: 4px 0;
  font-size: 0.875rem;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: bold;
  margin-right: 8px;
  background: #e0e0e0;
  color: #666;
}

.rank-gold {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  color: #000;
}

.rank-silver {
  background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%);
  color: #000;
}

.rank-bronze {
  background: linear-gradient(135deg, #cd7f32 0%, #e8a87c 100%);
  color: #fff;
}

.participant-avatar {
  font-size: 1.2rem;
  margin-right: 6px;
}

.participant-name {
  flex: 1;
  font-weight: 500;
  max-width: 120px;
}

.participant-points {
  font-weight: bold;
  color: #667eea;
  margin-left: 8px;
}
</style>
