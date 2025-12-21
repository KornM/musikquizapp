<template>
  <v-app>
    <v-app-bar color="deep-purple-darken-2" prominent class="app-bar-gradient">
      <v-icon size="40" class="ml-2 mr-3">mdi-domain</v-icon>
      <v-app-bar-title class="text-h5 font-weight-bold">
        🏢 Tenant Management
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
                  >mdi-office-building</v-icon
                >
                <h2 class="text-h4 font-weight-bold mb-4 text-white">
                  Manage Tenants
                </h2>
                <p class="text-h6 mb-6 text-white">
                  Create and manage organizations
                </p>
                <v-btn
                  color="white"
                  size="x-large"
                  prepend-icon="mdi-plus-circle"
                  @click="showCreateDialog = true"
                  class="create-btn"
                >
                  Create New Tenant
                </v-btn>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <loading-spinner v-if="loading" message="Loading tenants..." />

        <error-alert v-else-if="error" :message="error" />

        <v-row v-else>
          <v-col cols="12">
            <v-card elevation="4">
              <v-card-title class="bg-deep-purple-lighten-1 text-white">
                <v-icon class="mr-2">mdi-format-list-bulleted</v-icon>
                All Tenants
              </v-card-title>
              <v-card-text class="pa-0">
                <v-data-table
                  :headers="headers"
                  :items="tenants"
                  :items-per-page="10"
                  class="elevation-0"
                >
                  <template v-slot:item.status="{ item }">
                    <v-chip
                      :color="item.status === 'active' ? 'success' : 'error'"
                      size="small"
                      variant="flat"
                    >
                      {{ item.status }}
                    </v-chip>
                  </template>
                  <template v-slot:item.createdAt="{ item }">
                    {{ formatDate(item.createdAt) }}
                  </template>
                  <template v-slot:item.actions="{ item }">
                    <v-btn
                      icon
                      size="small"
                      variant="text"
                      color="primary"
                      @click="viewAdmins(item)"
                      title="View Admins"
                    >
                      <v-icon>mdi-account-multiple</v-icon>
                    </v-btn>
                    <v-btn
                      icon
                      size="small"
                      variant="text"
                      color="primary"
                      @click="editTenant(item)"
                      title="Edit"
                    >
                      <v-icon>mdi-pencil</v-icon>
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
                      <v-icon size="64" color="grey">mdi-domain-off</v-icon>
                      <p class="text-h6 mt-4">No tenants yet</p>
                      <p class="text-body-2">
                        Create your first tenant to get started
                      </p>
                    </div>
                  </template>
                </v-data-table>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- Create/Edit Tenant Dialog -->
        <v-dialog v-model="showCreateDialog" max-width="600">
          <v-card>
            <v-card-title class="bg-deep-purple-lighten-1 text-white">
              <v-icon class="mr-2">{{
                editMode ? "mdi-pencil" : "mdi-plus"
              }}</v-icon>
              {{ editMode ? "Edit Tenant" : "Create New Tenant" }}
            </v-card-title>
            <v-card-text class="pt-6">
              <v-form ref="tenantForm" v-model="formValid">
                <v-text-field
                  v-model="tenantForm.name"
                  label="Tenant Name"
                  :rules="[rules.required]"
                  variant="outlined"
                  prepend-inner-icon="mdi-domain"
                  required
                />
                <v-textarea
                  v-model="tenantForm.description"
                  label="Description (Optional)"
                  variant="outlined"
                  prepend-inner-icon="mdi-text"
                  rows="3"
                />
                <v-select
                  v-if="editMode"
                  v-model="tenantForm.status"
                  label="Status"
                  :items="['active', 'inactive']"
                  variant="outlined"
                  prepend-inner-icon="mdi-check-circle"
                />
              </v-form>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn @click="closeDialog" variant="text">Cancel</v-btn>
              <v-btn
                color="primary"
                @click="saveTenant"
                :disabled="!formValid"
                :loading="saving"
              >
                {{ editMode ? "Update" : "Create" }}
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
                Are you sure you want to delete tenant "{{
                  tenantToDelete?.name
                }}"?
              </p>
              <p class="text-error mt-2">This action cannot be undone.</p>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn @click="showDeleteDialog = false" variant="text"
                >Cancel</v-btn
              >
              <v-btn color="error" @click="deleteTenant" :loading="deleting">
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
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import api from "@/services/api";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import ErrorAlert from "@/components/common/ErrorAlert.vue";
import SuccessSnackbar from "@/components/common/SuccessSnackbar.vue";

const router = useRouter();
const authStore = useAuthStore();

const loading = ref(false);
const error = ref(null);
const tenants = ref([]);
const showCreateDialog = ref(false);
const showDeleteDialog = ref(false);
const showSuccess = ref(false);
const successMessage = ref("");
const saving = ref(false);
const deleting = ref(false);
const formValid = ref(false);
const editMode = ref(false);
const tenantToDelete = ref(null);

const tenantForm = ref({
  name: "",
  description: "",
  status: "active",
});

const headers = [
  { title: "Name", key: "name", sortable: true },
  { title: "Description", key: "description", sortable: false },
  { title: "Status", key: "status", sortable: true },
  { title: "Created", key: "createdAt", sortable: true },
  { title: "Actions", key: "actions", sortable: false, align: "center" },
];

const rules = {
  required: (value) => !!value || "This field is required",
};

onMounted(() => {
  fetchTenants();
});

const fetchTenants = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await api.getTenants();
    tenants.value = response.data.tenants || [];
  } catch (err) {
    error.value =
      err.response?.data?.error?.message || "Failed to load tenants";
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

const editTenant = (tenant) => {
  editMode.value = true;
  tenantForm.value = {
    tenantId: tenant.tenantId,
    name: tenant.name,
    description: tenant.description || "",
    status: tenant.status,
  };
  showCreateDialog.value = true;
};

const closeDialog = () => {
  showCreateDialog.value = false;
  editMode.value = false;
  tenantForm.value = {
    name: "",
    description: "",
    status: "active",
  };
};

const saveTenant = async () => {
  saving.value = true;
  try {
    if (editMode.value) {
      await api.updateTenant(tenantForm.value.tenantId, {
        name: tenantForm.value.name,
        description: tenantForm.value.description,
        status: tenantForm.value.status,
      });
      successMessage.value = "Tenant updated successfully!";
    } else {
      await api.createTenant({
        name: tenantForm.value.name,
        description: tenantForm.value.description,
      });
      successMessage.value = "Tenant created successfully!";
    }
    showSuccess.value = true;
    closeDialog();
    await fetchTenants();
  } catch (err) {
    error.value = err.response?.data?.error?.message || "Failed to save tenant";
  } finally {
    saving.value = false;
  }
};

const confirmDelete = (tenant) => {
  tenantToDelete.value = tenant;
  showDeleteDialog.value = true;
};

const deleteTenant = async () => {
  deleting.value = true;
  try {
    await api.deleteTenant(tenantToDelete.value.tenantId);
    successMessage.value = "Tenant deleted successfully!";
    showSuccess.value = true;
    showDeleteDialog.value = false;
    await fetchTenants();
  } catch (err) {
    error.value =
      err.response?.data?.error?.message || "Failed to delete tenant";
  } finally {
    deleting.value = false;
  }
};

const viewAdmins = (tenant) => {
  router.push(`/super-admin/tenants/${tenant.tenantId}/admins`);
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
