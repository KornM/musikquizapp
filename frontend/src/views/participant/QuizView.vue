<template>
  <v-app>
    <v-app-bar color="deep-purple-darken-2" class="app-bar-gradient">
      <v-icon size="35" class="ml-2 mr-2 rotating-icon">mdi-music-note</v-icon>
      <v-app-bar-title class="font-weight-bold">
        {{ session?.title || "🎵 Music Quiz" }}
      </v-app-bar-title>
      <v-spacer />
      <v-btn icon variant="text" @click="goToLobby" title="Back to Lobby">
        <v-icon>mdi-home</v-icon>
      </v-btn>
      <v-chip color="yellow-darken-2" class="mr-2 points-chip" size="large">
        <v-icon start class="bounce-icon">mdi-trophy</v-icon>
        <span class="text-h6 font-weight-bold">{{ totalPoints }}</span>
      </v-chip>
      <v-chip
        color="white"
        variant="flat"
        size="large"
        class="profile-chip"
        @click="goToProfile"
        style="cursor: pointer"
      >
        <span class="text-h6 mr-2">{{ participantAvatar }}</span>
        <span class="font-weight-bold">{{ participantName }}</span>
        <v-icon end size="small">mdi-pencil</v-icon>
      </v-chip>
    </v-app-bar>

    <v-main class="participant-background">
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
          <v-card
            v-if="currentRound && roundStarted"
            class="mb-4 quiz-card"
            elevation="12"
          >
            <div class="round-header">
              <v-icon size="40" color="white" class="pulse-icon"
                >mdi-help-circle</v-icon
              >
              <span class="text-h5 font-weight-bold text-white ml-3">
                Round {{ currentRound.roundNumber }}
              </span>
            </div>

            <v-card-text class="pa-6">
              <!-- Question -->
              <v-alert
                type="info"
                variant="tonal"
                class="mb-6 question-alert"
                elevation="4"
              >
                <v-icon size="30" class="mr-3">mdi-comment-question</v-icon>
                <span class="text-h6 font-weight-medium">{{
                  currentRound.question
                }}</span>
              </v-alert>

              <v-alert
                v-if="submitted"
                :type="earnedPoints > 0 ? 'success' : 'error'"
                class="mb-6 result-alert"
                elevation="8"
              >
                <div class="text-center">
                  <div class="result-emoji">
                    {{ earnedPoints > 0 ? "🎉" : "😢" }}
                  </div>
                  <div class="text-h5 font-weight-bold mb-2">
                    {{ earnedPoints > 0 ? "Correct!" : "Wrong Answer" }}
                  </div>
                  <div class="text-h3 font-weight-bold mb-2">
                    {{ earnedPoints > 0 ? `+${earnedPoints}` : "0" }} points
                  </div>
                  <div v-if="earnedPoints === 10" class="text-h6">
                    ⚡ Lightning Fast! ⚡
                  </div>
                  <div v-else-if="earnedPoints === 8" class="text-h6">
                    🚀 Great Timing! 🚀
                  </div>
                  <div v-else-if="earnedPoints === 5" class="text-h6">
                    ✓ Nice Job! ✓
                  </div>
                  <div v-else class="text-h6">Better luck next time! 💪</div>
                </div>
              </v-alert>

              <v-form v-else @submit.prevent="submitAnswer">
                <p class="text-h6 mb-4 font-weight-bold">
                  <v-icon color="primary" class="mr-2"
                    >mdi-cursor-pointer</v-icon
                  >
                  Select your answer:
                </p>
                <v-radio-group v-model="selectedAnswer" :disabled="submitting">
                  <v-card
                    v-for="(answer, index) in currentRound.answers"
                    :key="index"
                    :class="[
                      'answer-option mb-3',
                      { selected: selectedAnswer === index },
                    ]"
                    @click="selectedAnswer = index"
                    elevation="4"
                  >
                    <v-card-text class="d-flex align-center pa-4">
                      <v-avatar
                        :color="getAnswerColor(index)"
                        size="50"
                        class="mr-4"
                      >
                        <span class="text-h5 font-weight-bold">
                          {{ String.fromCharCode(65 + index) }}
                        </span>
                      </v-avatar>
                      <span class="text-h6">{{ answer }}</span>
                      <v-spacer />
                      <v-radio :value="index" class="radio-hidden" />
                    </v-card-text>
                  </v-card>
                </v-radio-group>

                <v-btn
                  type="submit"
                  color="success"
                  size="x-large"
                  block
                  :loading="submitting"
                  :disabled="selectedAnswer === null"
                  class="submit-btn mt-4"
                  elevation="8"
                >
                  <v-icon start size="30">mdi-send</v-icon>
                  <span class="text-h6">Submit Answer</span>
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

// Load participant info from localStorage
const globalParticipantId = localStorage.getItem("globalParticipantId");
const globalParticipantToken = localStorage.getItem("globalParticipantToken");
const participantName = ref(localStorage.getItem("participantName") || "Guest");
const participantAvatar = ref(
  localStorage.getItem("participantAvatar") || "😀"
);

const selectedAnswer = ref(null);
const submitting = ref(false);
const submitted = ref(false);
const earnedPoints = ref(null);
const totalPoints = ref(0);
const roundStarted = ref(false);
const sessionJoined = ref(false);

let pollInterval = null;

const loadSession = async () => {
  try {
    const response = await api.getSession(sessionId);
    session.value = response.data;

    console.log("Session data:", session.value);
    console.log("Session status:", session.value.status);
    console.log("Current round number:", session.value.currentRound);
    console.log("Available rounds:", session.value.rounds);

    // Check if session is completed - redirect to lobby
    if (session.value.status === "completed") {
      console.log("Session is completed, redirecting to lobby");
      router.push("/lobby");
      return;
    }

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
    const myScore = scoreboard.find(
      (s) => s.participantId === globalParticipantId
    );
    if (myScore) {
      totalPoints.value = myScore.totalPoints;
    }
  } catch (err) {
    console.error("Error loading score:", err);
  }
};

const autoJoinSession = async () => {
  if (!globalParticipantToken) {
    console.error("No global participant token found");
    return false;
  }

  try {
    console.log("Auto-joining session:", sessionId);
    await api.joinSession(sessionId, globalParticipantToken);
    sessionJoined.value = true;
    console.log("Successfully joined session");
    return true;
  } catch (err) {
    // If already joined (409 conflict), that's okay - the endpoint is idempotent
    if (
      err.response?.status === 409 ||
      err.response?.data?.error?.code === "ALREADY_JOINED"
    ) {
      console.log("Already joined session (idempotent)");
      sessionJoined.value = true;
      return true;
    }
    console.error("Error joining session:", err);
    error.value =
      err.response?.data?.error?.message || "Failed to join session";
    return false;
  }
};

const goToProfile = () => {
  router.push("/profile");
};

const goToLobby = () => {
  router.push("/lobby");
};

const getAnswerColor = (index) => {
  const colors = [
    "deep-purple",
    "pink",
    "indigo",
    "cyan",
    "teal",
    "orange",
    "deep-orange",
    "blue-grey",
  ];
  return colors[index % colors.length];
};

const submitAnswer = async () => {
  if (selectedAnswer.value === null) return;

  submitting.value = true;
  try {
    const response = await api.submitAnswer(
      globalParticipantId,
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
  console.log("Global Participant ID:", globalParticipantId);
  console.log("Session ID:", sessionId);

  // Check if user has a global participant ID
  if (!globalParticipantId || !globalParticipantToken) {
    console.log("No global participant ID, redirecting to lobby");
    router.push("/lobby");
    return;
  }

  loading.value = true;

  // Auto-join the session
  const joined = await autoJoinSession();
  if (!joined) {
    loading.value = false;
    return;
  }

  // Load session data
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
.participant-background {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

.app-bar-gradient {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
}

.rotating-icon {
  animation: rotate 4s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.bounce-icon {
  animation: bounce 1s ease-in-out infinite;
}

@keyframes bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}

.points-chip {
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%,
  100% {
    box-shadow: 0 0 10px rgba(255, 193, 7, 0.5);
  }
  50% {
    box-shadow: 0 0 20px rgba(255, 193, 7, 0.8);
  }
}

.profile-chip {
  border: 2px solid #ffd700;
}

.quiz-card {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border-radius: 20px !important;
  overflow: hidden;
}

.round-header {
  background: rgba(0, 0, 0, 0.3);
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pulse-icon {
  animation: pulse-scale 1.5s ease-in-out infinite;
}

@keyframes pulse-scale {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.2);
  }
}

.question-alert {
  background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%) !important;
  border-radius: 15px !important;
  border-left: 5px solid #00bcd4 !important;
}

.result-alert {
  border-radius: 20px !important;
  animation: result-pop 0.5s ease-out;
}

@keyframes result-pop {
  0% {
    transform: scale(0.8);
    opacity: 0;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.result-emoji {
  font-size: 5rem;
  animation: emoji-bounce 0.6s ease-out;
}

@keyframes emoji-bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  25% {
    transform: translateY(-30px);
  }
  50% {
    transform: translateY(-15px);
  }
  75% {
    transform: translateY(-7px);
  }
}

.answer-option {
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 15px !important;
  border: 3px solid transparent;
}

.answer-option:hover {
  transform: translateX(10px) scale(1.02);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3) !important;
}

.answer-option.selected {
  border-color: #4caf50;
  background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);
  transform: scale(1.05);
}

.radio-hidden {
  opacity: 0;
}

.submit-btn {
  background: linear-gradient(90deg, #4caf50 0%, #8bc34a 100%) !important;
  border-radius: 15px !important;
  animation: button-glow 2s ease-in-out infinite;
}

@keyframes button-glow {
  0%,
  100% {
    box-shadow: 0 0 15px rgba(76, 175, 80, 0.5);
  }
  50% {
    box-shadow: 0 0 30px rgba(76, 175, 80, 0.8);
  }
}

.welcome-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 20px !important;
}

.music-notes {
  font-size: 4rem;
  display: flex;
  justify-content: center;
  gap: 2rem;
}

.note {
  display: inline-block;
  animation: float 3s ease-in-out infinite;
  filter: drop-shadow(0 0 10px rgba(255, 255, 255, 0.5));
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
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-30px) rotate(10deg);
  }
}
</style>
