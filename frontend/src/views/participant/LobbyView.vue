<template>
  <v-app>
    <v-app-bar color="deep-purple-darken-2" class="app-bar-gradient">
      <v-icon size="35" class="ml-2 mr-2">mdi-music-note</v-icon>
      <v-app-bar-title class="font-weight-bold">
        🎵 Music Quiz Lobby
      </v-app-bar-title>
      <v-spacer />
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

    <v-main class="lobby-background">
      <v-container>
        <!-- Welcome Card -->
        <v-row class="mb-6">
          <v-col>
            <v-card class="welcome-card" elevation="8">
              <v-card-text class="text-center pa-8">
                <div class="welcome-avatar mb-4">{{ participantAvatar }}</div>
                <h2 class="text-h4 font-weight-bold mb-2 text-white">
                  Welcome, {{ participantName }}!
                </h2>
                <p class="text-h6 text-white mb-4">Ready to join a quiz?</p>
                <v-chip color="white" variant="outlined" size="large">
                  <v-icon start>mdi-domain</v-icon>
                  {{ tenantName || "Loading..." }}
                </v-chip>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <loading-spinner v-if="loading" message="Loading sessions..." />

        <error-alert v-else-if="error" :message="error" />

        <div v-else>
          <!-- Active Sessions -->
          <v-row v-if="activeSessions.length > 0">
            <v-col cols="12">
              <h2 class="text-h5 font-weight-bold mb-4 d-flex align-center">
                <v-icon color="success" class="mr-2 pulse-icon"
                  >mdi-play-circle</v-icon
                >
                Active Quizzes
              </h2>
            </v-col>
            <v-col
              v-for="session in activeSessions"
              :key="session.sessionId"
              cols="12"
              md="6"
              lg="4"
            >
              <v-card elevation="8" hover class="session-card active-session">
                <div class="card-header active-header">
                  <v-icon size="50" color="white" class="pulse-icon"
                    >mdi-music-note</v-icon
                  >
                  <v-chip color="success" class="status-chip" size="small">
                    <v-icon start size="small">mdi-circle</v-icon>
                    LIVE
                  </v-chip>
                </div>

                <v-card-title class="pt-4">
                  {{ session.title }}
                </v-card-title>

                <v-card-text>
                  <p class="text-body-2 mb-3">{{ session.description }}</p>
                  <v-chip size="small" color="primary" variant="tonal">
                    <v-icon start size="small">mdi-music-circle</v-icon>
                    {{ session.roundCount }} rounds
                  </v-chip>
                </v-card-text>

                <v-card-actions>
                  <v-btn
                    color="success"
                    size="large"
                    block
                    prepend-icon="mdi-play"
                    @click="joinSession(session.sessionId)"
                    :loading="joiningSession === session.sessionId"
                  >
                    Join Quiz
                  </v-btn>
                </v-card-actions>
              </v-card>
            </v-col>
          </v-row>

          <!-- Upcoming/Draft Sessions -->
          <v-row v-if="upcomingSessions.length > 0" class="mt-6">
            <v-col cols="12">
              <h2 class="text-h5 font-weight-bold mb-4 d-flex align-center">
                <v-icon color="warning" class="mr-2">mdi-clock-outline</v-icon>
                Coming Soon
              </h2>
            </v-col>
            <v-col
              v-for="session in upcomingSessions"
              :key="session.sessionId"
              cols="12"
              md="6"
              lg="4"
            >
              <v-card elevation="4" class="session-card upcoming-session">
                <div class="card-header upcoming-header">
                  <v-icon size="50" color="white">mdi-clock-outline</v-icon>
                </div>

                <v-card-title class="pt-4">
                  {{ session.title }}
                </v-card-title>

                <v-card-text>
                  <p class="text-body-2 mb-3">{{ session.description }}</p>
                  <v-chip size="small" color="warning" variant="tonal">
                    <v-icon start size="small">mdi-clock</v-icon>
                    Not started yet
                  </v-chip>
                </v-card-text>

                <v-card-actions>
                  <v-btn
                    color="grey"
                    size="large"
                    block
                    disabled
                    prepend-icon="mdi-clock-outline"
                  >
                    Waiting to Start
                  </v-btn>
                </v-card-actions>
              </v-card>
            </v-col>
          </v-row>

          <!-- No Sessions -->
          <v-row
            v-if="activeSessions.length === 0 && upcomingSessions.length === 0"
          >
            <v-col cols="12">
              <v-card class="text-center pa-8" elevation="4">
                <v-icon size="80" color="grey-lighten-1"
                  >mdi-music-note-off</v-icon
                >
                <h3 class="text-h5 mt-4 mb-2">No Quizzes Available</h3>
                <p class="text-body-1 text-grey">
                  Check back soon! The quiz master will start a session shortly.
                </p>
                <v-btn
                  color="primary"
                  variant="tonal"
                  class="mt-4"
                  prepend-icon="mdi-refresh"
                  @click="loadSessions"
                >
                  Refresh
                </v-btn>
              </v-card>
            </v-col>
          </v-row>
        </div>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import api from "@/services/api";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import ErrorAlert from "@/components/common/ErrorAlert.vue";

const router = useRouter();

// Load participant info from localStorage
const globalParticipantId = localStorage.getItem("globalParticipantId");
const globalParticipantToken = localStorage.getItem("globalParticipantToken");
const globalParticipantTenantId = localStorage.getItem(
  "globalParticipantTenantId"
);
const participantName = ref(localStorage.getItem("participantName") || "Guest");
const participantAvatar = ref(
  localStorage.getItem("participantAvatar") || "😀"
);

const sessions = ref([]);
const loading = ref(false);
const error = ref(null);
const joiningSession = ref(null);
const tenantName = ref("");

let pollInterval = null;

// Computed properties for filtering sessions
const activeSessions = computed(() => {
  return sessions.value.filter((s) => s.status === "active");
});

const upcomingSessions = computed(() => {
  return sessions.value.filter((s) => s.status === "draft");
});

onMounted(async () => {
  // Check if user has a global participant ID
  if (
    !globalParticipantId ||
    !globalParticipantToken ||
    !globalParticipantTenantId
  ) {
    console.log("No global participant ID, redirecting to registration");
    router.push("/register");
    return;
  }

  // Load tenant info
  try {
    const response = await api.getGlobalParticipant(globalParticipantId);
    const profile = response.data;
    participantName.value = profile.name;
    participantAvatar.value = profile.avatar;

    // Update localStorage
    localStorage.setItem("participantName", profile.name);
    localStorage.setItem("participantAvatar", profile.avatar);
  } catch (err) {
    console.error("Failed to load participant profile:", err);
  }

  // Load sessions
  await loadSessions();

  // Poll for updates every 5 seconds
  pollInterval = setInterval(() => {
    loadSessions();
  }, 5000);
});

onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval);
  }
});

const loadSessions = async () => {
  loading.value = true;
  error.value = null;

  try {
    const response = await api.getSessions();
    // The API returns { sessions: [...] }
    const allSessions = response.data.sessions || response.data || [];

    // Filter sessions by tenant
    sessions.value = allSessions.filter(
      (session) => session.tenantId === globalParticipantTenantId
    );

    // Get tenant name from first session if available
    if (sessions.value.length > 0 && sessions.value[0].tenantName) {
      tenantName.value = sessions.value[0].tenantName;
    }
  } catch (err) {
    console.error("Failed to load sessions:", err);
    error.value =
      err.response?.data?.error?.message || "Failed to load sessions";
  } finally {
    loading.value = false;
  }
};

const joinSession = async (sessionId) => {
  joiningSession.value = sessionId;

  try {
    // Auto-join the session
    await api.joinSession(sessionId, globalParticipantToken);

    // Navigate to quiz view
    router.push(`/quiz/${sessionId}`);
  } catch (err) {
    // If already joined (409 conflict), that's okay - just navigate
    if (
      err.response?.status === 409 ||
      err.response?.data?.error?.code === "ALREADY_JOINED"
    ) {
      router.push(`/quiz/${sessionId}`);
    } else {
      console.error("Error joining session:", err);
      error.value =
        err.response?.data?.error?.message || "Failed to join session";
    }
  } finally {
    joiningSession.value = null;
  }
};

const goToProfile = () => {
  router.push("/profile");
};
</script>

<style scoped>
.app-bar-gradient {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}

.lobby-background {
  background: linear-gradient(180deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

.welcome-card {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border-radius: 16px !important;
}

.welcome-avatar {
  font-size: 5rem;
  animation: avatar-bounce 2s ease-in-out infinite;
}

@keyframes avatar-bounce {
  0%,
  100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-10px) scale(1.1);
  }
}

.profile-chip {
  border: 2px solid #ffd700;
  transition: transform 0.2s;
}

.profile-chip:hover {
  transform: scale(1.05);
}

.session-card {
  border-radius: 16px !important;
  transition: transform 0.2s, box-shadow 0.2s;
  overflow: hidden;
}

.session-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2) !important;
}

.card-header {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.active-header {
  background: linear-gradient(135deg, #4caf50 0%, #8bc34a 100%);
}

.upcoming-header {
  background: linear-gradient(135deg, #ff9800 0%, #ffc107 100%);
}

.status-chip {
  position: absolute;
  top: 12px;
  right: 12px;
  font-weight: bold;
}

.pulse-icon {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.8;
  }
}

.active-session {
  border: 3px solid #4caf50;
}

.upcoming-session {
  opacity: 0.8;
}
</style>
