<template>
  <v-app>
    <v-app-bar color="deep-purple-darken-2" prominent class="app-bar-gradient">
      <v-icon size="40" class="ml-2 mr-3">mdi-music-box-multiple</v-icon>
      <v-app-bar-title class="text-h5 font-weight-bold">
        🎵 Katrin goes 49+1 Quiz Dashboard
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
        <v-row class="mb-4">
          <v-col>
            <v-card class="hero-card" elevation="6">
              <v-card-text class="text-center pa-4">
                <v-icon size="50" color="white" class="mb-2"
                  >mdi-music-note-plus</v-icon
                >
                <h2 class="text-h5 font-weight-bold mb-2 text-white">
                  Create Amazing Quizzes
                </h2>
                <p class="text-body-1 mb-4 text-white">
                  Music, Pictures, or Text - You Choose!
                </p>
                <v-btn
                  color="white"
                  size="large"
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
          <!-- Participant Registration Card -->
          <v-row class="mb-6">
            <v-col cols="12">
              <v-card elevation="4" class="registration-card">
                <v-card-text class="pa-6">
                  <div class="d-flex align-center">
                    <v-icon size="50" color="primary" class="mr-4"
                      >mdi-account-multiple-plus</v-icon
                    >
                    <div class="flex-grow-1">
                      <h3 class="text-h5 font-weight-bold mb-2">
                        Participant Registration
                      </h3>
                      <p class="text-body-1 mb-0">
                        Share this link with participants to register for your
                        quizzes
                      </p>
                    </div>
                    <div class="d-flex flex-column ga-2">
                      <v-btn
                        color="primary"
                        size="large"
                        prepend-icon="mdi-content-copy"
                        @click="copyRegistrationLink"
                        variant="elevated"
                      >
                        Copy Link
                      </v-btn>
                      <v-btn
                        color="secondary"
                        size="large"
                        prepend-icon="mdi-qrcode"
                        @click="showRegistrationQR = true"
                        variant="outlined"
                      >
                        Show QR Code
                      </v-btn>
                    </div>
                  </div>
                  <v-text-field
                    :model-value="registrationUrl"
                    readonly
                    variant="outlined"
                    density="compact"
                    class="mt-4"
                    hide-details
                  />
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>

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
                @updated="handleSessionUpdated"
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

        <!-- Registration QR Code Dialog -->
        <v-dialog v-model="showRegistrationQR" max-width="500">
          <v-card>
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2">mdi-qrcode</v-icon>
              Participant Registration QR Code
            </v-card-title>
            <v-card-text class="text-center pa-6">
              <div v-if="registrationQRCode" class="qr-code-container">
                <img
                  :src="registrationQRCode"
                  alt="Registration QR Code"
                  class="qr-code-image"
                />
              </div>
              <p class="text-body-2 mt-4">
                Participants can scan this QR code to register for your quizzes
              </p>
              <v-text-field
                :model-value="registrationUrl"
                readonly
                variant="outlined"
                density="compact"
                class="mt-4"
                hide-details
              />
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn variant="text" @click="showRegistrationQR = false"
                >Close</v-btn
              >
              <v-btn color="primary" @click="copyRegistrationLink"
                >Copy Link</v-btn
              >
            </v-card-actions>
          </v-card>
        </v-dialog>

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
const showRegistrationQR = ref(false);
const registrationQRCode = ref(null);

// Compute registration URL
const registrationUrl = computed(() => {
  const baseUrl = window.location.origin;
  const tenantId = authStore.tenantId;
  return `${baseUrl}/register?tenantId=${tenantId}`;
});

onMounted(() => {
  sessionsStore.fetchSessions();
  generateRegistrationQR();
});

const generateRegistrationQR = async () => {
  try {
    const QRCode = (await import("qrcode")).default;
    const url = registrationUrl.value;
    registrationQRCode.value = await QRCode.toDataURL(url, {
      width: 300,
      margin: 2,
      color: {
        dark: "#5E35B1",
        light: "#FFFFFF",
      },
    });
  } catch (err) {
    console.error("Failed to generate QR code:", err);
  }
};

const copyRegistrationLink = async () => {
  try {
    await navigator.clipboard.writeText(registrationUrl.value);
    successMessage.value = "Registration link copied to clipboard!";
    showSuccess.value = true;
  } catch (err) {
    console.error("Failed to copy link:", err);
    successMessage.value = "Failed to copy link";
    showSuccess.value = true;
  }
};

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

const handleSessionUpdated = async () => {
  successMessage.value = "Session updated successfully!";
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

.registration-card {
  border-radius: 12px !important;
  border-left: 5px solid #5e35b1;
  background: linear-gradient(135deg, #ffffff 0%, #f5f7fa 100%);
}

.qr-code-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.qr-code-image {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
}
</style>
