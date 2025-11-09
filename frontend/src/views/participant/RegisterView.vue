<template>
  <v-app>
    <v-main>
      <v-container class="fill-height" fluid>
        <v-row align="center" justify="center">
          <v-col cols="12" sm="8" md="6" lg="4">
            <v-card elevation="8">
              <v-card-title class="text-h5 text-center bg-primary">
                Join Music Quiz
              </v-card-title>

              <v-card-text class="pa-6">
                <loading-spinner v-if="loading" message="Loading session..." />

                <error-alert v-else-if="error" :message="error" />

                <div v-else-if="session">
                  <p class="text-h6 mb-2">{{ session.title }}</p>
                  <p class="text-body-2 mb-4">{{ session.description }}</p>

                  <v-form @submit.prevent="handleRegister">
                    <v-text-field
                      v-model="name"
                      label="Your Name"
                      variant="outlined"
                      :rules="[rules.required]"
                      :disabled="registering"
                      autofocus
                      class="mb-4"
                    />

                    <p class="text-subtitle-1 mb-2">Choose Your Avatar</p>
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
                      color="primary"
                      size="large"
                      block
                      :loading="registering"
                      :disabled="!name || !selectedAvatar"
                    >
                      Join Quiz
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
const session = ref(null);
const name = ref("");
const selectedAvatar = ref(null);
const loading = ref(false);
const error = ref(null);
const registering = ref(false);

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
  // Set default avatar
  selectedAvatar.value = avatars[0];

  if (!sessionId) {
    error.value = "No session ID provided";
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
  try {
    const response = await api.registerParticipant(
      sessionId,
      name.value,
      selectedAvatar.value
    );
    const { participantId, token } = response.data;

    // Store participant info including avatar
    localStorage.setItem("participantId", participantId);
    localStorage.setItem("participantToken", token);
    localStorage.setItem("participantName", name.value);
    localStorage.setItem("participantAvatar", selectedAvatar.value);

    // Redirect to participant quiz view
    router.push(`/quiz/${sessionId}`);
  } catch (err) {
    error.value = err.response?.data?.error?.message || "Failed to register";
  } finally {
    registering.value = false;
  }
};
</script>

<style scoped>
.avatar-card {
  cursor: pointer;
  transition: all 0.2s;
}

.avatar-card:hover {
  transform: scale(1.1);
}
</style>
