<template>
  <v-app>
    <v-main class="register-background">
      <v-container class="fill-height" fluid>
        <v-row align="center" justify="center">
          <v-col cols="12" sm="8" md="6" lg="4">
            <v-card elevation="12" class="register-card">
              <div class="card-header-gradient">
                <v-icon size="80" color="white" class="mb-3 header-icon"
                  >mdi-music-box-multiple</v-icon
                >
                <h2 class="text-h3 font-weight-bold text-white mb-2">
                  🎉 Join the Quiz! 🎉
                </h2>
                <p class="text-h6 text-white">Let's have some fun!</p>
              </div>

              <v-card-text class="pa-6">
                <loading-spinner v-if="loading" message="Loading session..." />

                <error-alert v-else-if="error" :message="error" />

                <div v-else-if="session">
                  <v-card class="mb-4 session-info-card" elevation="4">
                    <v-card-text>
                      <div class="d-flex align-center mb-2">
                        <v-icon color="deep-purple" size="30" class="mr-2"
                          >mdi-music-note-multiple</v-icon
                        >
                        <p class="text-h5 font-weight-bold mb-0">
                          {{ session.title }}
                        </p>
                      </div>
                      <p class="text-body-1">{{ session.description }}</p>
                    </v-card-text>
                  </v-card>

                  <v-alert
                    v-if="hasExistingProfile"
                    type="success"
                    variant="tonal"
                    class="mb-4"
                    prominent
                  >
                    <div class="d-flex align-center">
                      <v-icon size="30" class="mr-2">mdi-party-popper</v-icon>
                      <div>
                        <div class="text-h6 font-weight-bold">
                          Welcome back!
                        </div>
                        <div>Your profile has been loaded.</div>
                      </div>
                    </div>
                  </v-alert>

                  <v-form @submit.prevent="handleRegister">
                    <v-text-field
                      v-model="name"
                      label="Your Name"
                      variant="outlined"
                      :rules="[rules.required]"
                      :disabled="registering"
                      autofocus
                      class="mb-4"
                      prepend-inner-icon="mdi-account-circle"
                      color="deep-purple"
                    />

                    <p class="text-h6 mb-3 font-weight-bold">
                      <v-icon color="deep-purple" class="mr-2"
                        >mdi-emoticon-happy</v-icon
                      >
                      Choose Your Avatar
                    </p>
                    <v-item-group
                      v-model="selectedAvatar"
                      mandatory
                      class="mb-4"
                    >
                      <v-row>
                        <v-col
                          v-for="avatar in avatars"
                          :key="avatar"
                          cols="3"
                          sm="2"
                        >
                          <v-item
                            v-slot="{ isSelected, toggle }"
                            :value="avatar"
                          >
                            <v-card
                              :color="isSelected ? 'primary' : ''"
                              class="d-flex align-center justify-center avatar-card"
                              height="60"
                              @click="toggle"
                            >
                              <span class="text-h4">{{ avatar }}</span>
                            </v-card>
                          </v-item>
                        </v-col>
                      </v-row>
                    </v-item-group>

                    <v-btn
                      type="submit"
                      color="deep-purple"
                      size="x-large"
                      block
                      :loading="registering"
                      :disabled="!name || !selectedAvatar"
                      class="join-btn"
                      elevation="8"
                    >
                      <v-icon start size="30">mdi-rocket-launch</v-icon>
                      <span class="text-h6">Let's Go!</span>
                    </v-btn>
                  </v-form>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "@/services/api";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import ErrorAlert from "@/components/common/ErrorAlert.vue";

const route = useRoute();
const router = useRouter();

const sessionId = route.query.sessionId;
const tenantId = route.query.tenantId || route.query.tenant; // Support both parameter names
const session = ref(null);
const name = ref("");
const selectedAvatar = ref(null);
const loading = ref(false);
const error = ref(null);
const registering = ref(false);
const hasExistingProfile = ref(false);

const avatars = [
  "😀",
  "😎",
  "🤓",
  "🥳",
  "🤩",
  "😇",
  "🦸",
  "🦹",
  "🧙",
  "🧚",
  "🧛",
  "🧜",
  "🐶",
  "🐱",
  "🐭",
  "🐹",
  "🐰",
  "🦊",
  "🐻",
  "🐼",
  "🐨",
  "🐯",
  "🦁",
  "🐮",
  "🐷",
  "🐸",
  "🐵",
  "🐔",
  "🐧",
  "🦄",
];

const rules = {
  required: (value) => !!value || "Name is required",
};

onMounted(async () => {
  // Check for existing global participant ID in localStorage
  const savedParticipantId = localStorage.getItem("globalParticipantId");
  const savedToken = localStorage.getItem("globalParticipantToken");
  const savedTenantId = localStorage.getItem("globalParticipantTenantId");

  // If we have a saved participant ID and it matches the current tenant, load the profile
  if (savedParticipantId && savedToken && savedTenantId === tenantId) {
    try {
      const response = await api.getGlobalParticipant(savedParticipantId);
      const profile = response.data;
      name.value = profile.name;
      selectedAvatar.value = profile.avatar;
      hasExistingProfile.value = true;
    } catch (err) {
      console.log(
        "Could not load existing profile (token may have expired), showing registration form"
      );
      // If profile load fails (e.g., token expired), clear saved data and show registration form
      localStorage.removeItem("globalParticipantId");
      localStorage.removeItem("globalParticipantToken");
      localStorage.removeItem("globalParticipantTenantId");
      selectedAvatar.value = avatars[0];
      hasExistingProfile.value = false;
    }
  } else {
    // No saved profile or different tenant, show registration form
    selectedAvatar.value = avatars[0];
    hasExistingProfile.value = false;
  }

  if (!sessionId) {
    error.value = "No session ID provided";
    return;
  }

  if (!tenantId) {
    error.value =
      "No tenant ID provided. Please use the QR code or registration link.";
    return;
  }

  loading.value = true;
  try {
    const response = await api.getSession(sessionId);
    session.value = response.data;
  } catch (err) {
    error.value =
      err.response?.data?.error?.message || "Failed to load session";
  } finally {
    loading.value = false;
  }
});

const handleRegister = async () => {
  if (!name.value || !selectedAvatar.value) return;

  registering.value = true;
  error.value = null; // Clear previous errors

  try {
    // Check if we already have a global participant ID for this tenant
    const savedParticipantId = localStorage.getItem("globalParticipantId");
    const savedToken = localStorage.getItem("globalParticipantToken");
    const savedTenantId = localStorage.getItem("globalParticipantTenantId");

    let participantId, token;

    if (savedParticipantId && savedToken && savedTenantId === tenantId) {
      // Update existing profile
      await api.updateGlobalParticipant(savedParticipantId, {
        name: name.value,
        avatar: selectedAvatar.value,
      });
      participantId = savedParticipantId;
      token = savedToken;
    } else {
      // Register new global participant
      const response = await api.registerGlobalParticipant(
        tenantId,
        name.value,
        selectedAvatar.value
      );
      participantId = response.data.participantId;
      token = response.data.token;

      // Store global participant info
      localStorage.setItem("globalParticipantId", participantId);
      localStorage.setItem("globalParticipantToken", token);
      localStorage.setItem("globalParticipantTenantId", tenantId);
    }

    // Store current profile info for quick access
    localStorage.setItem("participantName", name.value);
    localStorage.setItem("participantAvatar", selectedAvatar.value);

    // Redirect to participant lobby to see all available sessions
    router.push("/lobby");
  } catch (err) {
    console.error("Registration error:", err);

    // Handle nickname taken error specifically
    if (err.response?.status === 409) {
      error.value =
        err.response?.data?.error?.message ||
        "This nickname is already taken. Please choose a different name.";
    } else {
      error.value =
        err.response?.data?.error?.message ||
        err.response?.data?.message ||
        "Failed to register";
    }
  } finally {
    registering.value = false;
  }
};
</script>

<style scoped>
.register-background {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  animation: gradient-shift 10s ease infinite;
  background-size: 200% 200%;
}

@keyframes gradient-shift {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

.register-card {
  border-radius: 20px !important;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3) !important;
  animation: card-float 3s ease-in-out infinite;
}

@keyframes card-float {
  0%,
  100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
}

.card-header-gradient {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  padding: 40px 20px;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.card-header-gradient::before {
  content: "🎵 🎶 🎤 🎸 🎹 🎺 🎻 🥁";
  position: absolute;
  top: 10px;
  left: -100%;
  width: 200%;
  font-size: 1.5rem;
  opacity: 0.3;
  animation: scroll-emojis 20s linear infinite;
}

@keyframes scroll-emojis {
  from {
    left: -100%;
  }
  to {
    left: 100%;
  }
}

.card-header-gradient v-icon {
  animation: icon-spin 4s ease-in-out infinite;
}

@keyframes icon-spin {
  0%,
  100% {
    transform: rotate(0deg) scale(1);
  }
  25% {
    transform: rotate(-10deg) scale(1.1);
  }
  75% {
    transform: rotate(10deg) scale(1.1);
  }
}

.avatar-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 12px !important;
  border: 2px solid transparent;
}

.avatar-card:hover {
  transform: scale(1.2) rotate(10deg);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
  border-color: #ffd700;
}

.v-card.v-theme--light.primary {
  animation: selected-pulse 1s ease-in-out infinite;
}

@keyframes selected-pulse {
  0%,
  100% {
    box-shadow: 0 0 10px rgba(103, 58, 183, 0.5);
  }
  50% {
    box-shadow: 0 0 20px rgba(103, 58, 183, 1);
  }
}

.join-btn {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
  border-radius: 15px !important;
  animation: button-pulse 2s ease-in-out infinite;
}

@keyframes button-pulse {
  0%,
  100% {
    box-shadow: 0 0 15px rgba(102, 126, 234, 0.5);
  }
  50% {
    box-shadow: 0 0 30px rgba(102, 126, 234, 0.8);
  }
}

.session-info-card {
  border-radius: 15px !important;
  border-left: 5px solid #673ab7;
}

.header-icon {
  animation: icon-wiggle 2s ease-in-out infinite;
}

@keyframes icon-wiggle {
  0%,
  100% {
    transform: rotate(0deg);
  }
  25% {
    transform: rotate(-15deg);
  }
  75% {
    transform: rotate(15deg);
  }
}
</style>
