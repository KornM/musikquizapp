<template>
  <v-app>
    <v-app-bar color="primary">
      <v-app-bar-title>{{ session?.title || "Music Quiz" }}</v-app-bar-title>
      <v-spacer />
      <v-chip color="success" class="mr-2" size="large">
        <v-icon start>mdi-trophy</v-icon>
        {{ totalPoints }} points
      </v-chip>
      <v-chip color="white" variant="outlined" size="large">
        <span class="text-h6 mr-2">{{ participantAvatar }}</span>
        {{ participantName }}
      </v-chip>
    </v-app-bar>

    <v-main>
      <v-container>
        <loading-spinner v-if="loading" message="Loading quiz..." />

        <error-alert v-else-if="error" :message="error" />

        <div v-else-if="session">
          <v-card class="mb-4">
            <v-card-text>
              <p class="text-h6">{{ session.title }}</p>
              <p class="text-body-2">{{ session.description }}</p>
              <v-chip size="small" class="mt-2">
                <v-icon start>mdi-music-circle</v-icon>
                {{ session.roundCount }} rounds
              </v-chip>
            </v-card-text>
          </v-card>

          <!-- Current Round Answer Form -->
          <v-card v-if="currentRound && roundStarted" class="mb-4">
            <v-card-title>Round {{ currentRound.roundNumber }}</v-card-title>
            <v-card-text>
              <!-- Question -->
              <v-alert type="info" variant="tonal" class="mb-4">
                <div class="text-h6">{{ currentRound.question }}</div>
              </v-alert>

              <v-alert
                v-if="submitted"
                :type="earnedPoints > 0 ? 'success' : 'error'"
                class="mb-4"
              >
                <div class="text-h6">Answer submitted!</div>
                <div v-if="earnedPoints > 0" class="text-h4 mt-2">
                  🎉 +{{ earnedPoints }} points!
                </div>
                <div v-else class="text-h4 mt-2">
                  ❌ Wrong answer - 0 points
                </div>
                <div v-if="earnedPoints === 10" class="text-subtitle-1">
                  Lightning fast! ⚡
                </div>
                <div v-else-if="earnedPoints === 8" class="text-subtitle-1">
                  Great timing! 🚀
                </div>
                <div v-else-if="earnedPoints === 5" class="text-subtitle-1">
                  Correct! ✓
                </div>
              </v-alert>

              <v-form v-else @submit.prevent="submitAnswer">
                <p class="text-subtitle-1 mb-4">Select your answer:</p>
                <v-radio-group v-model="selectedAnswer" :disabled="submitting">
                  <v-radio
                    v-for="(answer, index) in currentRound.answers"
                    :key="index"
                    :label="`${String.fromCharCode(65 + index)}: ${answer}`"
                    :value="index"
                  />
                </v-radio-group>

                <v-btn
                  type="submit"
                  color="primary"
                  size="large"
                  block
                  :loading="submitting"
                  :disabled="selectedAnswer === null"
                >
                  Submit Answer
                </v-btn>
              </v-form>
            </v-card-text>
          </v-card>

          <!-- Waiting for Round -->
          <v-card v-else class="welcome-card" elevation="8">
            <v-card-text class="text-center pa-8">
              <!-- Music Animation -->
              <div class="music-notes mb-6">
                <span class="note">🎵</span>
                <span class="note">🎶</span>
                <span class="note">🎵</span>
              </div>

              <!-- Welcome Message -->
              <div class="text-h4 mb-4 font-weight-bold">
                Welcome to the Music Quiz!
              </div>

              <!-- Participant Info -->
              <v-card class="mx-auto mb-6" max-width="400" elevation="4">
                <v-card-text class="pa-6">
                  <div class="text-h3 mb-3">{{ participantAvatar }}</div>
                  <div class="text-h5 font-weight-bold mb-2">
                    {{ participantName }}
                  </div>
                  <v-divider class="my-4"></v-divider>
                  <div class="d-flex align-center justify-center">
                    <v-icon color="yellow-darken-2" size="32" class="mr-2"
                      >mdi-trophy</v-icon
                    >
                    <span class="text-h4 font-weight-bold">{{
                      totalPoints
                    }}</span>
                    <span class="text-h6 ml-2">points</span>
                  </div>
                </v-card-text>
              </v-card>

              <!-- Status Message -->
              <v-alert
                type="info"
                variant="tonal"
                class="mx-auto"
                max-width="500"
              >
                <div class="text-h6 mb-2">🎤 Get Ready!</div>
                <p class="text-body-1">
                  The quiz master will start the next round soon...
                </p>
                <p class="text-body-2 mt-2">
                  Listen carefully and answer quickly to earn more points!
                </p>
              </v-alert>

              <div class="mt-4">
                <p class="text-subtitle-1 mb-2">Session Information:</p>
                <v-list density="compact">
                  <v-list-item>
                    <template #prepend>
                      <v-icon>mdi-identifier</v-icon>
                    </template>
                    <v-list-item-title>Session ID</v-list-item-title>
                    <v-list-item-subtitle>{{
                      session.sessionId
                    }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <template #prepend>
                      <v-icon>mdi-music-note-multiple</v-icon>
                    </template>
                    <v-list-item-title>Total Rounds</v-list-item-title>
                    <v-list-item-subtitle>{{
                      session.roundCount
                    }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <template #prepend>
                      <v-icon>mdi-information</v-icon>
                    </template>
                    <v-list-item-title>Status</v-list-item-title>
                    <v-list-item-subtitle>{{
                      session.status
                    }}</v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </div>
            </v-card-text>
          </v-card>
        </div>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "@/services/api";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import ErrorAlert from "@/components/common/ErrorAlert.vue";

const route = useRoute();
const router = useRouter();

const sessionId = route.params.id;
const session = ref(null);
const currentRound = ref(null);
const loading = ref(false);
const error = ref(null);
const participantName = ref(localStorage.getItem("participantName") || "Guest");
const participantAvatar = ref(
  localStorage.getItem("participantAvatar") || "😀"
);
const participantId = localStorage.getItem("participantId");

const selectedAnswer = ref(null);
const submitting = ref(false);
const submitted = ref(false);
const earnedPoints = ref(null);
const totalPoints = ref(0);
const roundStarted = ref(false);

let pollInterval = null;

const loadSession = async () => {
  try {
    const response = await api.getSession(sessionId);
    session.value = response.data;

    console.log("Session data:", session.value);
    console.log("Current round number:", session.value.currentRound);
    console.log("Available rounds:", session.value.rounds);

    // Check if there's a current round
    if (session.value.currentRound) {
      const round = session.value.rounds?.find(
        (r) => r.roundNumber === session.value.currentRound
      );
      console.log("Found round:", round);

      // Check if round has been started (has roundStartedAt timestamp)
      const isRoundStarted = !!session.value.roundStartedAt;
      roundStarted.value = isRoundStarted;
      console.log("Round started:", isRoundStarted);

      if (
        round &&
        (!currentRound.value ||
          currentRound.value.roundNumber !== round.roundNumber)
      ) {
        currentRound.value = round;
        selectedAnswer.value = null;
        submitted.value = false;
        earnedPoints.value = null;
        console.log("Set current round:", currentRound.value);
      }
    } else {
      currentRound.value = null;
      roundStarted.value = false;
      console.log("No current round active");
    }

    // Load participant's total score from backend
    await loadParticipantScore();
  } catch (err) {
    console.error("Error loading session:", err);
  }
};

const loadParticipantScore = async () => {
  try {
    const response = await api.getScoreboard(sessionId);
    const scoreboard = response.data.scoreboard;
    const myScore = scoreboard.find((s) => s.participantId === participantId);
    if (myScore) {
      totalPoints.value = myScore.totalPoints;
    }
  } catch (err) {
    console.error("Error loading score:", err);
  }
};

const submitAnswer = async () => {
  if (selectedAnswer.value === null) return;

  submitting.value = true;
  try {
    const response = await api.submitAnswer(
      participantId,
      sessionId,
      currentRound.value.roundNumber,
      selectedAnswer.value
    );
    submitted.value = true;
    earnedPoints.value = response.data.points;
    // Reload score from backend to ensure accuracy
    await loadParticipantScore();
  } catch (err) {
    error.value =
      err.response?.data?.error?.message || "Failed to submit answer";
  } finally {
    submitting.value = false;
  }
};

onMounted(async () => {
  console.log("QuizView mounted");
  console.log("Participant ID:", participantId);
  console.log("Session ID:", sessionId);

  // Check if user is registered
  if (!participantId) {
    console.log("No participant ID, redirecting to registration");
    router.push(`/register?sessionId=${sessionId}`);
    return;
  }

  loading.value = true;
  console.log("Loading initial session data...");
  await loadSession();
  loading.value = false;
  console.log("Initial load complete");

  // Poll for updates every 3 seconds
  console.log("Starting polling interval...");
  pollInterval = setInterval(() => {
    console.log("Polling for updates...");
    loadSession();
  }, 3000);
});

onUnmounted(() => {
  console.log("QuizView unmounting, clearing interval");
  if (pollInterval) {
    clearInterval(pollInterval);
  }
});
</script>

<style scoped>
.welcome-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.music-notes {
  font-size: 3rem;
  display: flex;
  justify-content: center;
  gap: 2rem;
}

.note {
  display: inline-block;
  animation: float 3s ease-in-out infinite;
}

.note:nth-child(1) {
  animation-delay: 0s;
}

.note:nth-child(2) {
  animation-delay: 1s;
}

.note:nth-child(3) {
  animation-delay: 2s;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-20px);
  }
}
</style>
