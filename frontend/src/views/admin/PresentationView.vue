<template>
  <div class="presentation-view" @keydown.esc="exitPresentation">
    <loading-spinner v-if="loading" message="Loading session..." />

    <div
      v-else-if="session && session.rounds && session.rounds.length > 0"
      class="fullscreen"
    >
      <!-- Header -->
      <v-app-bar color="primary" density="compact">
        <v-btn icon @click="exitPresentation">
          <v-icon>mdi-close</v-icon>
        </v-btn>
        <v-app-bar-title>{{ session.title }}</v-app-bar-title>
        <v-spacer />
        <v-chip class="mr-4">
          Round {{ currentRoundIndex + 1 }} of {{ session.rounds.length }}
        </v-chip>
      </v-app-bar>

      <!-- Main Content -->
      <v-container fluid class="fill-height pa-8 pt-12">
        <v-row class="fill-height">
          <!-- Scoreboard -->
          <v-col cols="12" md="3">
            <v-card elevation="4" class="scoreboard-card">
              <v-card-title class="text-h6 bg-primary">
                <v-icon start>mdi-trophy</v-icon>
                Scoreboard
              </v-card-title>
              <v-card-text class="pa-0">
                <v-list density="compact">
                  <v-list-item
                    v-for="(entry, index) in scoreboard"
                    :key="entry.participantId"
                    :class="{ 'bg-yellow-lighten-4': index === 0 }"
                  >
                    <template #prepend>
                      <v-avatar
                        :color="index === 0 ? 'yellow-darken-2' : 'grey'"
                        size="32"
                      >
                        <span class="text-h6">{{ entry.avatar || "😀" }}</span>
                      </v-avatar>
                    </template>
                    <v-list-item-title>
                      <span class="font-weight-bold">{{ entry.name }}</span>
                    </v-list-item-title>
                    <v-list-item-subtitle>
                      {{ entry.correctAnswers }} correct
                    </v-list-item-subtitle>
                    <template #append>
                      <v-chip color="primary" size="small">
                        {{ entry.totalPoints }}
                      </v-chip>
                    </template>
                  </v-list-item>
                  <v-list-item v-if="scoreboard.length === 0">
                    <v-list-item-title class="text-center text-grey">
                      No participants yet
                    </v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- Quiz Content -->
          <v-col cols="12" md="9">
            <!-- Question (always visible for admin) -->
            <v-card class="mb-6" elevation="4">
              <v-card-text class="text-center">
                <div class="text-h4 font-weight-bold mb-4">
                  {{ currentRound.question }}
                </div>
              </v-card-text>
            </v-card>

            <!-- Audio Player (only if session requires audio) -->
            <v-card
              v-if="session.requiresAudio !== false"
              class="mb-6"
              elevation="4"
            >
              <v-card-text class="text-center">
                <v-icon size="64" color="primary" class="mb-4"
                  >mdi-music-circle</v-icon
                >
                <audio
                  ref="audioPlayer"
                  :src="currentAudioUrl"
                  controls
                  class="audio-player"
                  @play="handleAudioPlay"
                />
              </v-card-text>
            </v-card>

            <!-- Answers -->
            <v-row>
              <v-col
                v-for="(answer, index) in currentRound.answers"
                :key="index"
                cols="12"
                md="6"
              >
                <v-card
                  :color="getAnswerColor(index)"
                  :class="[
                    'answer-card',
                    {
                      'correct-answer':
                        showAnswer && index === currentRound.correctAnswer,
                    },
                  ]"
                  elevation="8"
                >
                  <v-card-text class="text-center">
                    <div class="answer-letter">
                      {{ String.fromCharCode(65 + index) }}
                    </div>
                    <div class="answer-text">{{ answer }}</div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>

            <!-- Controls -->
            <v-row class="mt-6">
              <v-col cols="12" class="text-center">
                <v-btn
                  size="large"
                  color="secondary"
                  class="mr-4"
                  @click="previousRound"
                  :disabled="currentRoundIndex === 0"
                >
                  <v-icon start>mdi-chevron-left</v-icon>
                  Previous
                </v-btn>

                <v-btn
                  size="large"
                  color="primary"
                  class="mr-4"
                  @click="startRound"
                  :loading="startingRound"
                >
                  <v-icon start>mdi-play</v-icon>
                  Start Round for Participants
                </v-btn>

                <v-btn
                  size="large"
                  :color="showAnswer ? 'warning' : 'success'"
                  class="mr-4"
                  @click="toggleAnswer"
                >
                  <v-icon start>{{
                    showAnswer ? "mdi-eye-off" : "mdi-eye"
                  }}</v-icon>
                  {{ showAnswer ? "Hide" : "Reveal" }} Answer
                </v-btn>

                <v-btn
                  size="large"
                  color="secondary"
                  @click="nextRound"
                  :disabled="currentRoundIndex === session.rounds.length - 1"
                >
                  Next
                  <v-icon end>mdi-chevron-right</v-icon>
                </v-btn>
              </v-col>
            </v-row>
          </v-col>
        </v-row>
      </v-container>
    </div>

    <v-container v-else-if="!loading">
      <v-alert type="info">
        No rounds available for this session. Please add rounds first.
      </v-alert>
      <v-btn @click="exitPresentation" class="mt-4">Back to Session</v-btn>
    </v-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useSessionsStore } from "@/stores/sessions";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import api from "@/services/api";

const route = useRoute();
const router = useRouter();
const sessionsStore = useSessionsStore();

const sessionId = route.params.id;
const loading = ref(false);
const currentRoundIndex = ref(0);
const showAnswer = ref(false);
const currentAudioUrl = ref(null);
const startingRound = ref(false);
const scoreboard = ref([]);

let scoreboardInterval = null;

const session = computed(() => sessionsStore.currentSession);
const currentRound = computed(
  () => session.value?.rounds?.[currentRoundIndex.value]
);

const loadScoreboard = async () => {
  try {
    const response = await api.getScoreboard(sessionId);
    scoreboard.value = response.data.scoreboard;
  } catch (error) {
    console.error("Failed to load scoreboard:", error);
  }
};

onMounted(async () => {
  loading.value = true;
  await sessionsStore.fetchSession(sessionId);
  loading.value = false;

  if (currentRound.value) {
    loadAudio();
  }

  // Load scoreboard initially
  await loadScoreboard();

  // Poll scoreboard every 5 seconds
  scoreboardInterval = setInterval(loadScoreboard, 5000);
});

onUnmounted(() => {
  if (scoreboardInterval) {
    clearInterval(scoreboardInterval);
  }
});

const loadAudio = async () => {
  if (currentRound.value?.audioKey) {
    try {
      const response = await api.getAudioUrl(currentRound.value.audioKey);
      currentAudioUrl.value = response.data.url;
    } catch (error) {
      console.error("Failed to load audio:", error);
    }
  }
};

const getAnswerColor = (index) => {
  if (showAnswer.value && index === currentRound.value.correctAnswer) {
    return "success";
  }
  return "white";
};

const toggleAnswer = () => {
  showAnswer.value = !showAnswer.value;
};

const nextRound = () => {
  if (currentRoundIndex.value < session.value.rounds.length - 1) {
    currentRoundIndex.value++;
    showAnswer.value = false;
    loadAudio();
  }
};

const previousRound = () => {
  if (currentRoundIndex.value > 0) {
    currentRoundIndex.value--;
    showAnswer.value = false;
    loadAudio();
  }
};

const handleAudioPlay = () => {
  // Automatically start the round when audio plays
  if (currentRound.value) {
    startRound();
  }
};

const startRound = async () => {
  if (!currentRound.value) return;

  startingRound.value = true;
  try {
    await api.startRound(sessionId, currentRound.value.roundNumber);
    console.log(
      `Started round ${currentRound.value.roundNumber} for participants`
    );
  } catch (error) {
    console.error("Failed to start round:", error);
    alert("Failed to start round for participants");
  } finally {
    startingRound.value = false;
  }
};

const exitPresentation = () => {
  router.push(`/admin/sessions/${sessionId}`);
};
</script>

<style scoped>
.presentation-view {
  background: #1a1a1a;
  min-height: 100vh;
}

.fullscreen {
  min-height: 100vh;
}

.scoreboard-card {
  max-height: calc(100vh - 120px);
  overflow-y: auto;
}

.audio-player {
  width: 100%;
  max-width: 600px;
}

.answer-card {
  min-height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  cursor: default;
}

.answer-card.correct-answer {
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

.answer-letter {
  font-size: 3rem;
  font-weight: bold;
  color: #1976d2;
  margin-bottom: 1rem;
}

.answer-text {
  font-size: 1.5rem;
  font-weight: 500;
}

.fill-height {
  min-height: calc(100vh - 48px);
}
</style>
