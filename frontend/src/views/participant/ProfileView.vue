<template>
  <v-app>
    <v-app-bar color="deep-purple-darken-2" class="app-bar-gradient">
      <v-btn icon @click="goBack">
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <v-app-bar-title class="font-weight-bold"> My Profile </v-app-bar-title>
    </v-app-bar>

    <v-main class="profile-background">
      <v-container class="fill-height" fluid>
        <v-row align="center" justify="center">
          <v-col cols="12" sm="8" md="6" lg="4">
            <v-card elevation="12" class="profile-card">
              <div class="card-header-gradient">
                <v-icon size="80" color="white" class="mb-3 header-icon"
                  >mdi-account-circle</v-icon
                >
                <h2 class="text-h3 font-weight-bold text-white mb-2">
                  Edit Your Profile
                </h2>
                <p class="text-h6 text-white">Update your name and avatar</p>
              </div>

              <v-card-text class="pa-6">
                <loading-spinner v-if="loading" message="Loading profile..." />

                <error-alert v-else-if="error" :message="error" />

                <div v-else>
                  <v-alert
                    v-if="successMessage"
                    type="success"
                    variant="tonal"
                    class="mb-4"
                    closable
                    @click:close="successMessage = null"
                  >
                    {{ successMessage }}
                  </v-alert>

                  <v-form @submit.prevent="handleUpdate">
                    <v-text-field
                      v-model="name"
                      label="Your Name"
                      variant="outlined"
                      :rules="[rules.required]"
                      :disabled="updating"
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
                      :loading="updating"
                      :disabled="!name || !selectedAvatar"
                      class="update-btn"
                      elevation="8"
                    >
                      <v-icon start size="30">mdi-content-save</v-icon>
                      <span class="text-h6">Save Changes</span>
                    </v-btn>
                  </v-form>

                  <v-divider class="my-6"></v-divider>

                  <div class="text-center">
                    <p class="text-body-2 text-grey mb-2">
                      Profile Information
                    </p>
                    <v-chip class="mb-2" size="small">
                      <v-icon start size="small">mdi-identifier</v-icon>
                      ID: {{ participantId?.substring(0, 8) }}...
                    </v-chip>
                  </div>
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
import { useRouter } from "vue-router";
import api from "@/services/api";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import ErrorAlert from "@/components/common/ErrorAlert.vue";

const router = useRouter();

const participantId = localStorage.getItem("globalParticipantId");
const name = ref("");
const selectedAvatar = ref(null);
const loading = ref(false);
const error = ref(null);
const updating = ref(false);
const successMessage = ref(null);

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

const goBack = () => {
  router.back();
};

onMounted(async () => {
  // Check if user has a global participant ID
  if (!participantId) {
    error.value = "No profile found. Please register first.";
    return;
  }

  loading.value = true;
  try {
    const response = await api.getGlobalParticipant(participantId);
    const profile = response.data;
    name.value = profile.name;
    selectedAvatar.value = profile.avatar;
  } catch (err) {
    error.value =
      err.response?.data?.error?.message || "Failed to load profile";
  } finally {
    loading.value = false;
  }
});

const handleUpdate = async () => {
  if (!name.value || !selectedAvatar.value) return;

  updating.value = true;
  error.value = null;
  successMessage.value = null;

  try {
    await api.updateGlobalParticipant(participantId, {
      name: name.value,
      avatar: selectedAvatar.value,
    });

    // Update localStorage with new profile
    localStorage.setItem("participantName", name.value);
    localStorage.setItem("participantAvatar", selectedAvatar.value);

    successMessage.value = "Profile updated successfully! 🎉";
  } catch (err) {
    error.value =
      err.response?.data?.error?.message || "Failed to update profile";
  } finally {
    updating.value = false;
  }
};
</script>

<style scoped>
.profile-background {
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

.app-bar-gradient {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
}

.profile-card {
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

.header-icon {
  animation: icon-pulse 2s ease-in-out infinite;
}

@keyframes icon-pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
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

.update-btn {
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
</style>
