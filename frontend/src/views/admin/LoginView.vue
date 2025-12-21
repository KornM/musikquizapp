<template>
  <v-container fluid class="fill-height">
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card elevation="12">
          <v-card-title class="text-h4 text-center py-6 bg-primary">
            <span class="text-white">Music Quiz Admin</span>
          </v-card-title>

          <v-card-text class="pa-6">
            <error-alert v-if="error" :message="error" @close="error = null" />

            <!-- Success message showing tenant name -->
            <v-alert
              v-if="showTenantInfo && authStore.tenantName"
              type="success"
              variant="tonal"
              class="mb-4"
            >
              <div class="text-subtitle-1">
                <v-icon class="mr-2">mdi-domain</v-icon>
                Logged in to: <strong>{{ authStore.tenantName }}</strong>
              </div>
            </v-alert>

            <v-form ref="formRef" @submit.prevent="handleLogin">
              <v-text-field
                v-model="username"
                label="Username"
                prepend-icon="mdi-account"
                :rules="[rules.required]"
                variant="outlined"
                class="mb-3"
              />

              <v-text-field
                v-model="password"
                label="Password"
                prepend-icon="mdi-lock"
                :type="showPassword ? 'text' : 'password'"
                :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                @click:append="showPassword = !showPassword"
                :rules="[rules.required]"
                variant="outlined"
                class="mb-3"
              />

              <v-btn
                type="submit"
                color="primary"
                block
                size="large"
                :loading="loading"
              >
                Login
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import ErrorAlert from "@/components/common/ErrorAlert.vue";

const router = useRouter();
const authStore = useAuthStore();

const formRef = ref(null);
const username = ref("");
const password = ref("");
const showPassword = ref(false);
const loading = ref(false);
const error = ref(null);
const showTenantInfo = ref(false);

const rules = {
  required: (value) => !!value || "This field is required",
};

const handleLogin = async () => {
  const { valid } = await formRef.value.validate();
  if (!valid) return;

  loading.value = true;
  error.value = null;

  const result = await authStore.login(username.value, password.value);

  loading.value = false;

  if (result.success) {
    // Show tenant info briefly before redirecting
    showTenantInfo.value = true;
    setTimeout(() => {
      router.push("/admin/dashboard");
    }, 1000);
  } else {
    error.value = result.error;
  }
};
</script>

<style scoped>
.fill-height {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
</style>
