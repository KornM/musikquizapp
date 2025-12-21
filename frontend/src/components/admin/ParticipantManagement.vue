<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      <v-icon start>mdi-account-group</v-icon>
      Participants
      <v-spacer />
      <v-chip color="primary" class="mr-2">
        {{ participants.length }} registered
      </v-chip>
      <v-btn
        color="error"
        variant="text"
        @click="confirmClearAll"
        :disabled="participants.length === 0"
      >
        Clear All
      </v-btn>
    </v-card-title>

    <v-card-text>
      <loading-spinner v-if="loading" message="Loading participants..." />

      <error-alert v-else-if="error" :message="error" />

      <v-list v-else-if="participants.length > 0">
        <v-list-item
          v-for="(participant, index) in participants"
          :key="participant.participantId"
          :class="{ 'bg-yellow-lighten-5': index === 0 }"
        >
          <template #prepend>
            <v-avatar
              :color="index === 0 ? 'yellow-darken-2' : 'grey'"
              size="40"
            >
              <span class="text-h6">{{ participant.avatar }}</span>
            </v-avatar>
          </template>

          <v-list-item-title>
            <span class="font-weight-bold">{{ participant.name }}</span>
          </v-list-item-title>

          <v-list-item-subtitle>
            {{ participant.totalPoints || 0 }} points •
            {{ participant.correctAnswers || 0 }} correct
          </v-list-item-subtitle>

          <template #append>
            <v-btn
              icon="mdi-pencil"
              size="small"
              variant="text"
              @click="openEditDialog(participant)"
            />
            <v-btn
              icon="mdi-delete"
              size="small"
              variant="text"
              color="error"
              @click="confirmDelete(participant)"
            />
          </template>
        </v-list-item>
      </v-list>

      <v-alert v-else type="info" variant="tonal">
        No participants registered yet
      </v-alert>
    </v-card-text>

    <!-- Edit Dialog -->
    <v-dialog v-model="editDialog" max-width="500">
      <v-card>
        <v-card-title>Edit Participant</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="editForm.name"
            label="Name"
            variant="outlined"
            class="mb-4"
          />

          <p class="text-subtitle-1 mb-2">Avatar</p>
          <v-item-group v-model="editForm.avatar" mandatory>
            <v-row>
              <v-col v-for="avatar in avatars" :key="avatar" cols="2">
                <v-item v-slot="{ isSelected, toggle }" :value="avatar">
                  <v-card
                    :color="isSelected ? 'primary' : ''"
                    class="d-flex align-center justify-center"
                    height="50"
                    @click="toggle"
                  >
                    <span class="text-h5">{{ avatar }}</span>
                  </v-card>
                </v-item>
              </v-col>
            </v-row>
          </v-item-group>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="editDialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="saveEdit" :loading="saving"
            >Save</v-btn
          >
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title>Delete Participant?</v-card-title>
        <v-card-text>
          Are you sure you want to delete
          <strong>{{ deleteTarget?.name }}</strong
          >? This will also delete all their answers.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">Cancel</v-btn>
          <v-btn color="error" @click="deleteParticipant" :loading="deleting">
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Clear All Confirmation Dialog -->
    <v-dialog v-model="clearAllDialog" max-width="400">
      <v-card>
        <v-card-title>Clear All Participants?</v-card-title>
        <v-card-text>
          Are you sure you want to remove all
          {{ participants.length }} participants? This will also delete all
          their answers. This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="clearAllDialog = false">Cancel</v-btn>
          <v-btn color="error" @click="clearAll" :loading="clearing">
            Clear All
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup>
import { ref, onMounted } from "vue";
import api from "@/services/api";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import ErrorAlert from "@/components/common/ErrorAlert.vue";

const props = defineProps({
  sessionId: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(["updated"]);

const participants = ref([]);
const loading = ref(false);
const error = ref(null);
const editDialog = ref(false);
const deleteDialog = ref(false);
const clearAllDialog = ref(false);
const saving = ref(false);
const deleting = ref(false);
const clearing = ref(false);

const editForm = ref({
  participantId: null,
  name: "",
  avatar: "",
});

const deleteTarget = ref(null);

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
];

const loadParticipants = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await api.getParticipants(props.sessionId);
    participants.value = response.data.participants;
  } catch (err) {
    error.value =
      err.response?.data?.error?.message || "Failed to load participants";
  } finally {
    loading.value = false;
  }
};

const openEditDialog = (participant) => {
  editForm.value = {
    participantId: participant.participantId,
    name: participant.name,
    avatar: participant.avatar,
  };
  editDialog.value = true;
};

const saveEdit = async () => {
  saving.value = true;
  try {
    await api.updateParticipant(props.sessionId, editForm.value.participantId, {
      name: editForm.value.name,
      avatar: editForm.value.avatar,
    });
    editDialog.value = false;
    await loadParticipants();
    emit("updated");
  } catch (err) {
    error.value =
      err.response?.data?.error?.message || "Failed to update participant";
  } finally {
    saving.value = false;
  }
};

const confirmDelete = (participant) => {
  deleteTarget.value = participant;
  deleteDialog.value = true;
};

const deleteParticipant = async () => {
  deleting.value = true;
  try {
    await api.deleteParticipant(
      props.sessionId,
      deleteTarget.value.participantId
    );
    deleteDialog.value = false;
    await loadParticipants();
    emit("updated");
  } catch (err) {
    error.value =
      err.response?.data?.error?.message || "Failed to delete participant";
  } finally {
    deleting.value = false;
  }
};

const confirmClearAll = () => {
  clearAllDialog.value = true;
};

const clearAll = async () => {
  clearing.value = true;
  try {
    await api.clearParticipants(props.sessionId);
    clearAllDialog.value = false;
    await loadParticipants();
    emit("updated");
  } catch (err) {
    error.value =
      err.response?.data?.error?.message || "Failed to clear participants";
  } finally {
    clearing.value = false;
  }
};

onMounted(() => {
  loadParticipants();
});
</script>
