<template>
  <v-app>
    <v-app-bar color="deep-purple-darken-2" prominent class="app-bar-gradient">
      <v-icon size="40" class="ml-2 mr-3">mdi-music-box-multiple</v-icon>
      <v-app-bar-title class="text-h5 font-weight-bold">
        🎵 Music Quiz Dashboard
      </v-app-bar-title>
      <v-spacer />
      <!-- Display tenant name if available -->
      <div v-if="authStore.tenantName" class="mr-4 text-white">
        <v-chip color="white" variant="outlined" prepend-icon="mdi-domain">
          {{ authStore.tenantName }}
        </v-chip>
      </div>
      <v-btn icon @click="handleLogout" variant="text">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>

    <v-main class="main-background">
      <v-container>
        <!-- Hero Section -->
        <v-row class="mb-6">
          <v-col>
            <v-card class="hero-card" elevation="8">
              <v-card-text class="text-center pa-8">
                <v-icon size="80" color="white" class="mb-4"
                  >mdi-music-note-plus</v-icon
                >
                <h2 class="text-h4 font-weight-bold mb-4 text-white">
                  Create Amazing Quizzes
                </h2>
                <p class="text-h6 mb-6 text-white">
                  Music, Pictures, or Text - You Choose!
                </p>
                <v-btn
                  color="white"
                  size="x-large"
                  prepend-icon="mdi-plus-circle"
                  @click="showCreateDialog = true"
                  class="create-btn"
                >
                  Create New Session
                </v-btn>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <loading-spinner
          v-if="sessionsStore.loading"
          message="Loading sessions..."
        />

        <error-alert
          v-else-if="sessionsStore.error"
          :message="sessionsStore.error"
        />

        <div v-else>
          <!-- Global Scoreboard Section -->
          <v-row class="mb-6">
            <v-col cols="12">
              <h2 class="text-h5 font-weight-bold mb-4 d-flex align-center">
                <v-icon color="primary" class="mr-2">mdi-trophy-variant</v-icon>
                Global Leaderboard
              </h2>
            </v-col>
            <v-col cols="12">
              <GlobalScoreboardCard :tenant-id="authStore.tenantId" />
            </v-col>
          </v-row>

          <!-- All Sessions Section -->
          <v-row>
            <v-col cols="12">
              <h2 class="text-h5 font-weight-bold mb-4 d-flex align-center">
                <v-icon color="primary" class="mr-2"
                  >mdi-music-box-multiple</v-icon
                >
                All Quiz Sessions
              </h2>
            </v-col>
            <v-col
              v-for="session in sessionsStore.sessions"
              :key="session.sessionId"
              cols="12"
              sm="6"
              md="4"
            >
              <SessionCard
                :session="session"
                @deleted="handleSessionDeleted"
                @completed="handleSessionCompleted"
              />
            </v-col>

            <v-col v-if="sessionsStore.sessions.length === 0" cols="12">
              <v-card class="text-center pa-8">
                <v-icon size="64" color="grey">mdi-music-note-off</v-icon>
                <p class="text-h6 mt-4">No quiz sessions yet</p>
                <p class="text-body-2">
                  Create your first quiz session to get started
                </p>
              </v-card>
            </v-col>
          </v-row>
        </div>

        <session-form-dialog
          v-model="showCreateDialog"
          @created="handleSessionCreated"
        />

        <success-snackbar v-model="showSuccess" :message="successMessage" />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useSessionsStore } from "@/stores/sessions";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import ErrorAlert from "@/components/common/ErrorAlert.vue";
import SuccessSnackbar from "@/components/common/SuccessSnackbar.vue";
import SessionCard from "@/components/admin/SessionCard.vue";
import GlobalScoreboardCard from "@/components/admin/GlobalScoreboardCard.vue";
import SessionFormDialog from "@/components/admin/SessionFormDialog.vue";

const router = useRouter();
const authStore = useAuthStore();
const sessionsStore = useSessionsStore();

const showCreateDialog = ref(false);
const showSuccess = ref(false);
const successMessage = ref("");

onMounted(() => {
  sessionsStore.fetchSessions();
});

const handleLogout = () => {
  authStore.logout();
  router.push("/admin/login");
};

const handleSessionCreated = () => {
  showCreateDialog.value = false;
  successMessage.value = "Session created successfully!";
  showSuccess.value = true;
  sessionsStore.fetchSessions();
};

const handleSessionDeleted = async (sessionId) => {
  const result = await sessionsStore.deleteSession(sessionId);
  if (result.success) {
    successMessage.value = "Session deleted successfully!";
    showSuccess.value = true;
  }
};

const handleSessionCompleted = async () => {
  successMessage.value = "Session completed successfully!";
  showSuccess.value = true;
  sessionsStore.fetchSessions();
};
</script>

<style scoped>
.app-bar-gradient {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}

.main-background {
  background: linear-gradient(180deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

.hero-card {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border-radius: 16px !important;
}

.create-btn {
  font-weight: bold;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}
</style>
