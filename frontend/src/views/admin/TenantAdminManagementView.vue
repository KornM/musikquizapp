<template>
  <v-app>
    <v-app-bar color="deep-purple-darken-2" prominent class="app-bar-gradient">
      <v-btn icon @click="goBack" variant="text">
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <v-icon size="40" class="ml-2 mr-3">mdi-account-multiple</v-icon>
      <v-app-bar-title class="text-h5 font-weight-bold">
        👥 Tenant Admin Management
      </v-app-bar-title>
      <v-spacer />
      <v-btn icon @click="handleLogout" variant="text">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>

    <v-main class="main-background">
      <v-container>
        <!-- Header Section -->
        <v-row class="mb-6">
          <v-col>
            <v-card class="hero-card" elevation="8">
              <v-card-text class="text-center pa-8">
                <v-icon size="80" color="white" class="mb-4"
                  >mdi-account-supervisor</v-icon
                >
                <h2 class="text-h4 font-weight-bold mb-4 text-white">
                  Manage Admins for {{ tenantName }}
                </h2>
                <p class="text-h6 mb-6 text-white">
                  Create and manage administrator accounts
                </p>
                <v-btn
                  color="white"
                  size="x-large"
                  prepend-icon="mdi-plus-circle"
                  @click="showCreateDialog = true"
                  class="create-btn"
                >
                  Create New Admin
                </v-btn>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <loading-spinner v-if="loading" message="Loading admins..." />

        <error-alert v-else-if="error" :message="error" />

        <v-row v-else>
          <v-col cols="12">
            <v-card elevation="4">
              <v-card-title class="bg-deep-purple-lighten-1 text-white">
                <v-icon class="mr-2">mdi-format-list-bulleted</v-icon>
                Administrators
              </v-card-title>
              <v-card-text class="pa-0">
                <v-data-table
                  :headers="headers"
                  :items="admins"
                  :items-per-page="10"
                  class="elevation-0"
                >
                  <template v-slot:item.createdAt="{ item }">
                    {{ formatDate(item.createdAt) }}
                  </template>
                  <template v-slot:item.actions="{ item }">
                    <v-btn
                      icon
                      size="small"
                      variant="text"
                      color="primary"
                      @click="editAdmin(item)"
                      title="Edit"
                    >
                      <v-icon>mdi-pencil</v-icon>
                    </v-btn>
                    <v-btn
                      icon
                      size="small"
                      variant="text"
                      color="warning"
                      @click="resetPassword(item)"
                      title="Reset Password"
                    >
                      <v-icon>mdi-lock-reset</v-icon>
                    </v-btn>
                    <v-btn
                      icon
                      size="small"
                      variant="text"
                      color="error"
                      @click="confirmDelete(item)"
                      title="Delete"
                    >
                      <v-icon>mdi-delete</v-icon>
                    </v-btn>
                  </template>
                  <template v-slot:no-data>
                    <div class="text-center pa-8">
                      <v-icon size="64" color="grey">mdi-account-off</v-icon>
                      <p class="text-h6 mt-4">No admins yet</p>
                      <p class="text-body-2">
                        Create your first admin to get started
                      </p>
                    </div>
                  </template>
                </v-data-table>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- Create Admin Dialog -->
        <v-dialog v-model="showCreateDialog" max-width="600">
          <v-card>
            <v-card-title class="bg-deep-purple-lighten-1 text-white">
              <v-icon class="mr-2">mdi-plus</v-icon>
              Create New Admin
            </v-card-title>
            <v-card-text class="pt-6">
              <v-form ref="createForm" v-model="createFormValid">
                <v-text-field
                  v-model="createAdminForm.username"
                  label="Username"
                  :rules="[rules.required]"
                  variant="outlined"
                  prepend-inner-icon="mdi-account"
                  required
                />
                <v-text-field
                  v-model="createAdminForm.password"
                  label="Password"
                  type="password"
                  :rules="[rules.required, rules.minLength]"
                  variant="outlined"
                  prepend-inner-icon="mdi-lock"
                  required
                />
                <v-text-field
                  v-model="createAdminForm.email"
                  label="Email (Optional)"
                  type="email"
                  variant="outlined"
                  prepend-inner-icon="mdi-email"
                />
              </v-form>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn @click="closeCreateDialog" variant="text">Cancel</v-btn>
              <v-btn
                color="primary"
                @click="createAdmin"
                :disabled="!createFormValid"
                :loading="saving"
              >
                Create
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>

        <!-- Edit Admin Dialog -->
        <v-dialog v-model="showEditDialog" max-width="600">
          <v-card>
            <v-card-title class="bg-deep-purple-lighten-1 text-white">
              <v-icon class="mr-2">mdi-pencil</v-icon>
              Edit Admin
            </v-card-title>
            <v-card-text class="pt-6">
              <v-form ref="editForm" v-model="editFormValid">
                <v-text-field
                  v-model="editAdminForm.username"
                  label="Username"
                  :rules="[rules.required]"
                  variant="outlined"
                  prepend-inner-icon="mdi-account"
                  required
                />
                <v-text-field
                  v-model="editAdminForm.email"
                  label="Email"
                  type="email"
                  variant="outlined"
                  prepend-inner-icon="mdi-email"
                />
              </v-form>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn @click="closeEditDialog" variant="text">Cancel</v-btn>
              <v-btn
                color="primary"
                @click="updateAdmin"
                :disabled="!editFormValid"
                :loading="saving"
              >
                Update
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>

        <!-- Reset Password Dialog -->
        <v-dialog v-model="showPasswordDialog" max-width="500">
          <v-card>
            <v-card-title class="bg-warning text-white">
              <v-icon class="mr-2">mdi-lock-reset</v-icon>
              Reset Password
            </v-card-title>
            <v-card-text class="pt-6">
              <p class="mb-4">
                Reset password for "{{ adminToReset?.username }}"
              </p>
              <v-form ref="passwordForm" v-model="passwordFormValid">
                <v-text-field
                  v-model="newPassword"
                  label="New Password"
                  type="password"
                  :rules="[rules.required, rules.minLength]"
                  variant="outlined"
                  prepend-inner-icon="mdi-lock"
                  required
                />
              </v-form>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn @click="showPasswordDialog = false" variant="text"
                >Cancel</v-btn
              >
              <v-btn
                color="warning"
                @click="confirmResetPassword"
                :disabled="!passwordFormValid"
                :loading="resetting"
              >
                Reset Password
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>

        <!-- Delete Confirmation Dialog -->
        <v-dialog v-model="showDeleteDialog" max-width="500">
          <v-card>
            <v-card-title class="bg-error text-white">
              <v-icon class="mr-2">mdi-alert</v-icon>
              Confirm Delete
            </v-card-title>
            <v-card-text class="pt-6">
              <p>
                Are you sure you want to delete admin "{{
                  adminToDelete?.username
                }}"?
              </p>
              <p class="text-error mt-2">This action cannot be undone.</p>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn @click="showDeleteDialog = false" variant="text"
                >Cancel</v-btn
              >
              <v-btn color="error" @click="deleteAdmin" :loading="deleting">
                Delete
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>

        <success-snackbar v-model="showSuccess" :message="successMessage" />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import api from "@/services/api";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import ErrorAlert from "@/components/common/ErrorAlert.vue";
import SuccessSnackbar from "@/components/common/SuccessSnackbar.vue";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const tenantId = computed(() => route.params.tenantId);
const tenantName = ref("");
const loading = ref(false);
const error = ref(null);
const admins = ref([]);
const showCreateDialog = ref(false);
const showEditDialog = ref(false);
const showPasswordDialog = ref(false);
const showDeleteDialog = ref(false);
const showSuccess = ref(false);
const successMessage = ref("");
const saving = ref(false);
const resetting = ref(false);
const deleting = ref(false);
const createFormValid = ref(false);
const editFormValid = ref(false);
const passwordFormValid = ref(false);
const adminToDelete = ref(null);
const adminToReset = ref(null);
const newPassword = ref("");

const createAdminForm = ref({
  username: "",
  password: "",
  email: "",
});

const editAdminForm = ref({
  adminId: "",
  username: "",
  email: "",
});

const headers = [
  { title: "Username", key: "username", sortable: true },
  { title: "Email", key: "email", sortable: false },
  { title: "Created", key: "createdAt", sortable: true },
  { title: "Actions", key: "actions", sortable: false, align: "center" },
];

const rules = {
  required: (value) => !!value || "This field is required",
  minLength: (value) =>
    (value && value.length >= 8) || "Password must be at least 8 characters",
};

onMounted(async () => {
  await fetchTenantInfo();
  await fetchAdmins();
});

const fetchTenantInfo = async () => {
  try {
    const response = await api.getTenant(tenantId.value);
    tenantName.value = response.data.name;
  } catch (err) {
    tenantName.value = "Unknown Tenant";
  }
};

const fetchAdmins = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await api.getTenantAdmins(tenantId.value);
    admins.value = response.data.admins || [];
  } catch (err) {
    error.value = err.response?.data?.error?.message || "Failed to load admins";
  } finally {
    loading.value = false;
  }
};

const formatDate = (dateString) => {
  if (!dateString) return "N/A";
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
};

const closeCreateDialog = () => {
  showCreateDialog.value = false;
  createAdminForm.value = {
    username: "",
    password: "",
    email: "",
  };
};

const createAdmin = async () => {
  saving.value = true;
  try {
    await api.createTenantAdmin(tenantId.value, {
      username: createAdminForm.value.username,
      password: createAdminForm.value.password,
      email: createAdminForm.value.email,
    });
    successMessage.value = "Admin created successfully!";
    showSuccess.value = true;
    closeCreateDialog();
    await fetchAdmins();
  } catch (err) {
    error.value =
      err.response?.data?.error?.message || "Failed to create admin";
  } finally {
    saving.value = false;
  }
};

const editAdmin = (admin) => {
  editAdminForm.value = {
    adminId: admin.adminId,
    username: admin.username,
    email: admin.email || "",
  };
  showEditDialog.value = true;
};

const closeEditDialog = () => {
  showEditDialog.value = false;
  editAdminForm.value = {
    adminId: "",
    username: "",
    email: "",
  };
};

const updateAdmin = async () => {
  saving.value = true;
  try {
    await api.updateTenantAdmin(editAdminForm.value.adminId, {
      username: editAdminForm.value.username,
      email: editAdminForm.value.email,
      tenantId: tenantId.value,
    });
    successMessage.value = "Admin updated successfully!";
    showSuccess.value = true;
    closeEditDialog();
    await fetchAdmins();
  } catch (err) {
    error.value =
      err.response?.data?.error?.message || "Failed to update admin";
  } finally {
    saving.value = false;
  }
};

const resetPassword = (admin) => {
  adminToReset.value = admin;
  newPassword.value = "";
  showPasswordDialog.value = true;
};

const confirmResetPassword = async () => {
  resetting.value = true;
  try {
    await api.resetAdminPassword(adminToReset.value.adminId, newPassword.value);
    successMessage.value = "Password reset successfully!";
    showSuccess.value = true;
    showPasswordDialog.value = false;
    newPassword.value = "";
  } catch (err) {
    error.value =
      err.response?.data?.error?.message || "Failed to reset password";
  } finally {
    resetting.value = false;
  }
};

const confirmDelete = (admin) => {
  adminToDelete.value = admin;
  showDeleteDialog.value = true;
};

const deleteAdmin = async () => {
  deleting.value = true;
  try {
    await api.deleteTenantAdmin(adminToDelete.value.adminId);
    successMessage.value = "Admin deleted successfully!";
    showSuccess.value = true;
    showDeleteDialog.value = false;
    await fetchAdmins();
  } catch (err) {
    error.value =
      err.response?.data?.error?.message || "Failed to delete admin";
  } finally {
    deleting.value = false;
  }
};

const goBack = () => {
  router.push("/super-admin/tenants");
};

const handleLogout = () => {
  authStore.logout();
  router.push("/admin/login");
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
