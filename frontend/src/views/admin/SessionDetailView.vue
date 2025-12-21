<template>
  <v-app>
    <v-app-bar color="primary">
      <v-btn icon @click="$router.push('/admin/dashboard')">
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <v-app-bar-title>{{
        session?.title || "Session Details"
      }}</v-app-bar-title>
      <v-spacer />
      <v-btn icon @click="showQRDialog = true" v-if="session">
        <v-icon>mdi-qrcode</v-icon>
      </v-btn>
      <v-btn icon @click="presentSession" v-if="session">
        <v-icon>mdi-presentation</v-icon>
      </v-btn>
    </v-app-bar>

    <v-main>
      <v-container>
        <loading-spinner v-if="loading" message="Loading session..." />

        <error-alert v-else-if="error" :message="error" />

        <div v-else-if="session">
          <v-card class="mb-4">
            <v-card-text>
              <p class="text-h6">{{ session.title }}</p>
              <p class="text-body-2">{{ session.description }}</p>
              <v-chip class="mr-2" size="small">
                <v-icon start>mdi-music-circle</v-icon>
                {{ session.roundCount }} rounds
              </v-chip>
              <v-chip size="small" :color="statusColor">
                {{ session.status }}
              </v-chip>
            </v-card-text>
          </v-card>

          <v-card>
            <v-card-title class="d-flex align-center">
              <span>Quiz Rounds</span>
              <v-spacer />
              <v-btn
                color="primary"
                prepend-icon="mdi-plus"
                @click="showAddRound = true"
                :disabled="session.roundCount >= 30"
                class="mr-2"
              >
                Add Round
              </v-btn>
              <v-btn
                color="error"
                prepend-icon="mdi-delete-sweep"
                @click="confirmResetPoints"
                variant="outlined"
              >
                Reset All Points
              </v-btn>
            </v-card-title>

            <v-card-text>
              <v-alert
                v-if="session.roundCount >= 30"
                type="warning"
                class="mb-4"
              >
                Maximum of 30 rounds reached
              </v-alert>

              <RoundList
                :rounds="session.rounds || []"
                @delete="handleRoundDelete"
                @edit="handleRoundEdit"
              />

              <v-alert
                v-if="!session.rounds || session.rounds.length === 0"
                type="info"
              >
                No rounds yet. Add your first round to get started!
              </v-alert>
            </v-card-text>
          </v-card>

          <!-- Participants Management -->
          <v-card class="mt-4">
            <ParticipantManagement
              :session-id="sessionId"
              @updated="handleParticipantsUpdated"
            />
          </v-card>

          <!-- Scoreboard -->
          <v-card class="mt-4">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2">mdi-trophy</v-icon>
              <span>Live Scoreboard</span>
              <v-spacer />
              <v-btn
                icon
                size="small"
                @click="refreshScoreboard"
                :loading="loadingScoreboard"
              >
                <v-icon>mdi-refresh</v-icon>
              </v-btn>
            </v-card-title>

            <v-card-text>
              <loading-spinner
                v-if="loadingScoreboard"
                message="Loading scoreboard..."
              />

              <error-alert
                v-else-if="scoreboardError"
                :message="scoreboardError"
              />

              <div v-else-if="scoreboard && scoreboard.length > 0">
                <v-list>
                  <v-list-item
                    v-for="(participant, index) in scoreboard"
                    :key="participant.participantId"
                    class="scoreboard-item"
                  >
                    <template v-slot:prepend>
                      <v-avatar :color="getRankColor(index)" size="40">
                        <span class="text-h6">{{ index + 1 }}</span>
                      </v-avatar>
                    </template>

                    <v-list-item-title class="d-flex align-center">
                      <span class="text-h6 mr-2">{{ participant.avatar }}</span>
                      <span class="font-weight-bold">{{
                        participant.name
                      }}</span>
                    </v-list-item-title>

                    <v-list-item-subtitle>
                      {{ participant.correctAnswers }} correct answers
                    </v-list-item-subtitle>

                    <template v-slot:append>
                      <v-chip color="primary" size="large">
                        <span class="text-h6">{{
                          participant.totalPoints
                        }}</span>
                        <span class="text-caption ml-1">pts</span>
                      </v-chip>
                    </template>
                  </v-list-item>
                </v-list>
              </div>

              <v-alert v-else type="info">
                No participants have joined yet. Share the QR code to get
                started!
              </v-alert>
            </v-card-text>
          </v-card>
        </div>

        <RoundFormDialog
          v-model="showAddRound"
          :session-id="sessionId"
          :media-type="session?.mediaType || 'audio'"
          @created="handleRoundCreated"
        />

        <RoundFormDialog
          v-model="showEditRound"
          :media-type="session?.mediaType || 'audio'"
          :session-id="sessionId"
          :editing-round="editingRound"
          @created="handleRoundUpdated"
        />

        <QRCodeModal v-model="showQRDialog" :session-id="sessionId" />

        <SuccessSnackbar v-model="showSuccess" :message="successMessage" />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useSessionsStore } from "@/stores/sessions";
import api from "@/services/api";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import ErrorAlert from "@/components/common/ErrorAlert.vue";
import SuccessSnackbar from "@/components/common/SuccessSnackbar.vue";
import RoundList from "@/components/admin/RoundList.vue";
import RoundFormDialog from "@/components/admin/RoundFormDialog.vue";
import QRCodeModal from "@/components/admin/QRCodeModal.vue";
import ParticipantManagement from "@/components/admin/ParticipantManagement.vue";

const route = useRoute();
const router = useRouter();
const sessionsStore = useSessionsStore();

const sessionId = route.params.id;
const loading = ref(false);
const error = ref(null);
const showAddRound = ref(false);
const showEditRound = ref(false);
const editingRound = ref(null);
const showQRDialog = ref(false);
const showSuccess = ref(false);
const successMessage = ref("");
const scoreboard = ref([]);
const loadingScoreboard = ref(false);
const scoreboardError = ref(null);

const session = computed(() => sessionsStore.currentSession);

const statusColor = computed(() => {
  switch (session.value?.status) {
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

onMounted(async () => {
  loading.value = true;
  const result = await sessionsStore.fetchSession(sessionId);
  loading.value = false;

  if (!result.success) {
    error.value = result.error;
  } else {
    // Load scoreboard after session loads
    refreshScoreboard();
  }
});

const refreshScoreboard = async () => {
  loadingScoreboard.value = true;
  scoreboardError.value = null;
  try {
    const response = await api.getScoreboard(sessionId);
    scoreboard.value = response.data.participants || [];
  } catch (err) {
    scoreboardError.value =
      err.response?.data?.error?.message || "Failed to load scoreboard";
  } finally {
    loadingScoreboard.value = false;
  }
};

const getRankColor = (index) => {
  if (index === 0) return "gold";
  if (index === 1) return "silver";
  if (index === 2) return "#CD7F32"; // bronze
  return "grey";
};

const handleRoundCreated = () => {
  showAddRound.value = false;
  successMessage.value = "Round added successfully!";
  showSuccess.value = true;
  sessionsStore.fetchSession(sessionId);
};

const handleRoundEdit = (round) => {
  editingRound.value = round;
  showEditRound.value = true;
};

const handleRoundUpdated = () => {
  showEditRound.value = false;
  editingRound.value = null;
  successMessage.value = "Round updated successfully!";
  showSuccess.value = true;
  sessionsStore.fetchSession(sessionId);
};

const handleRoundDelete = async (roundId) => {
  const result = await sessionsStore.deleteRound(sessionId, roundId);
  if (result.success) {
    successMessage.value = "Round deleted successfully!";
    showSuccess.value = true;
    sessionsStore.fetchSession(sessionId);
  }
};

const confirmResetPoints = () => {
  if (
    confirm(
      "Are you sure you want to reset all points for all participants? This action cannot be undone."
    )
  ) {
    handleResetPoints();
  }
};

const handleResetPoints = async () => {
  try {
    await api.resetPoints(sessionId);
    successMessage.value = "All points have been reset!";
    showSuccess.value = true;
  } catch (err) {
    error.value =
      err.response?.data?.error?.message || "Failed to reset points";
  }
};

const handleParticipantsUpdated = () => {
  // Refresh session data and scoreboard when participants are updated
  sessionsStore.fetchSession(sessionId);
  refreshScoreboard();
};

const presentSession = () => {
  router.push(`/admin/sessions/${sessionId}/present`);
};
</script>

<style scoped>
.scoreboard-item {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

.scoreboard-item:last-child {
  border-bottom: none;
}
</style>
