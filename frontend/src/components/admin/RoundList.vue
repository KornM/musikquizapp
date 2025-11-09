<template>
  <v-list>
    <v-list-item
      v-for="round in rounds"
      :key="round.roundId"
      class="mb-2"
      border
    >
      <template #prepend>
        <v-avatar color="primary">
          {{ round.roundNumber }}
        </v-avatar>
      </template>

      <v-list-item-title> Round {{ round.roundNumber }} </v-list-item-title>

      <v-list-item-subtitle>
        <v-chip size="small" class="mr-1">
          <v-icon start size="small">mdi-music-circle</v-icon>
          {{ round.answers.length }} answers
        </v-chip>
      </v-list-item-subtitle>

      <template #append>
        <v-btn
          icon="mdi-pencil"
          variant="text"
          color="primary"
          size="small"
          class="mr-2"
          @click="emit('edit', round)"
        />
        <v-btn
          icon="mdi-delete"
          variant="text"
          color="error"
          size="small"
          @click="confirmDelete(round)"
        />
      </template>
    </v-list-item>
  </v-list>
</template>

<script setup>
defineProps({
  rounds: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["delete", "edit"]);

const confirmDelete = (round) => {
  if (confirm(`Are you sure you want to delete Round ${round.roundNumber}?`)) {
    emit("delete", round.roundId);
  }
};
</script>
