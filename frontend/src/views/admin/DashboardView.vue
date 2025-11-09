<template>
  <v-app>
    <v-app-bar color="primary" prominent>
      <v-app-bar-title>Music Quiz Dashboard</v-app-bar-title>
      <v-spacer />
      <v-btn icon @click="handleLogout">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>

    <v-main>
      <v-container>
        <v-row class="mb-4">
          <v-col>
            <v-btn
              color="primary"
              size="large"
              prepend-icon="mdi-plus"
              @click="showCreateDialog = true"
            >
              Create New Session
            </v-btn>
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

        <v-row v-else>
          <v-col
            v-for="session in sessionsStore.sessions"
            :key="session.sessionId"
            cols="12"
            sm="6"
            md="4"
          >
            <SessionCard :session="session" @deleted="handleSessionDeleted" />
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
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useSessionsStore } from "@/stores/sessions";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import ErrorAlert from "@/components/common/ErrorAlert.vue";
import SuccessSnackbar from "@/components/common/SuccessSnackbar.vue";
import SessionCard from "@/components/admin/SessionCard.vue";
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
</script>
