<template>
  <v-card elevation="8" class="scoreboard-card">
    <div class="card-header">
      <v-icon size="50" color="white" class="trophy-icon">mdi-trophy</v-icon>
    </div>

    <v-card-title class="d-flex align-center pt-4">
      <v-icon class="mr-2" color="primary">mdi-podium</v-icon>
      <span class="font-weight-bold">{{ session.title }}</span>
      <v-spacer />
      <v-btn
        icon
        size="small"
        variant="text"
        @click="refreshScoreboard"
        :loading="loading"
      >
        <v-icon>mdi-refresh</v-icon>
      </v-btn>
    </v-card-title>

    <v-card-text>
      <loading-spinner
        v-if="loading && !scoreboard.length"
        message="Loading scoreboard..."
        size="small"
      />

      <div v-else-if="scoreboard.length > 0">
        <!-- Top 3 Podium -->
        <div class="podium-container mb-4">
          <div v-if="scoreboard[1]" class="podium-place second">
            <div class="podium-avatar">{{ scoreboard[1].avatar }}</div>
            <div class="podium-name">{{ scoreboard[1].name }}</div>
            <div class="podium-points">{{ scoreboard[1].totalPoints }} pts</div>
            <div class="podium-rank">
              <v-icon color="silver">mdi-medal</v-icon>
              2nd
            </div>
          </div>

          <div v-if="scoreboard[0]" class="podium-place first">
            <div class="podium-crown">👑</div>
            <div class="podium-avatar">{{ scoreboard[0].avatar }}</div>
            <div class="podium-name">{{ scoreboard[0].name }}</div>
            <div class="podium-points">{{ scoreboard[0].totalPoints }} pts</div>
            <div class="podium-rank">
              <v-icon color="gold">mdi-medal</v-icon>
              1st
            </div>
          </div>

          <div v-if="scoreboard[2]" class="podium-place third">
            <div class="podium-avatar">{{ scoreboard[2].avatar }}</div>
            <div class="podium-name">{{ scoreboard[2].name }}</div>
            <div class="podium-points">{{ scoreboard[2].totalPoints }} pts</div>
            <div class="podium-rank">
              <v-icon color="bronze">mdi-medal</v-icon>
              3rd
            </div>
          </div>
        </div>

        <!-- Full Scoreboard List -->
        <v-list density="compact" class="scoreboard-list">
          <v-list-item
            v-for="(participant, index) in scoreboard"
            :key="participant.participantId"
            :class="['scoreboard-item', getRankClass(index)]"
          >
            <template #prepend>
              <div class="rank-badge" :class="getRankBadgeClass(index)">
                {{ index + 1 }}
              </div>
              <span class="participant-avatar ml-2">{{
                participant.avatar
              }}</span>
            </template>

            <v-list-item-title class="font-weight-medium">
              {{ participant.name }}
            </v-list-item-title>

            <template #append>
              <div class="d-flex align-center">
                <v-chip
                  size="small"
                  color="success"
                  variant="tonal"
                  class="mr-2"
                >
                  <v-icon start size="small">mdi-check-circle</v-icon>
                  {{ participant.correctAnswers }}
                </v-chip>
                <v-chip size="small" color="primary" variant="flat">
                  <v-icon start size="small">mdi-star</v-icon>
                  {{ participant.totalPoints }}
                </v-chip>
              </div>
            </template>
          </v-list-item>
        </v-list>
      </div>

      <div v-else class="text-center py-8">
        <v-icon size="64" color="grey-lighten-1">mdi-account-off</v-icon>
        <p class="text-h6 mt-4 text-grey">No participants yet</p>
        <p class="text-body-2 text-grey">
          Share the QR code to get players to join!
        </p>
      </div>
    </v-card-text>

    <v-card-actions>
      <v-btn
        variant="tonal"
        color="primary"
        prepend-icon="mdi-eye"
        @click="viewSession"
        block
      >
        View Session Details
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import api from "@/services/api";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";

const props = defineProps({
  session: {
    type: Object,
    required: true,
  },
});

const router = useRouter();
const scoreboard = ref([]);
const loading = ref(false);

onMounted(() => {
  refreshScoreboard();
});

const refreshScoreboard = async () => {
  loading.value = true;
  try {
    const response = await api.getScoreboard(props.session.sessionId);
    scoreboard.value = response.data.scoreboard || [];
  } catch (err) {
    console.error("Failed to load scoreboard:", err);
    scoreboard.value = [];
  } finally {
    loading.value = false;
  }
};

const getRankClass = (index) => {
  if (index === 0) return "rank-first";
  if (index === 1) return "rank-second";
  if (index === 2) return "rank-third";
  return "";
};

const getRankBadgeClass = (index) => {
  if (index === 0) return "badge-gold";
  if (index === 1) return "badge-silver";
  if (index === 2) return "badge-bronze";
  return "";
};

const viewSession = () => {
  router.push(`/admin/sessions/${props.session.sessionId}`);
};
</script>

<style scoped>
.scoreboard-card {
  border-radius: 16px !important;
  overflow: hidden;
}

.card-header {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.card-header::before {
  content: "🏆 🥇 🥈 🥉 ⭐ 🎖️";
  position: absolute;
  top: 50%;
  left: -100%;
  width: 200%;
  font-size: 2rem;
  opacity: 0.2;
  animation: scroll-icons 20s linear infinite;
  transform: translateY(-50%);
}

@keyframes scroll-icons {
  from {
    left: -100%;
  }
  to {
    left: 100%;
  }
}

.trophy-icon {
  animation: trophy-bounce 2s ease-in-out infinite;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));
}

@keyframes trophy-bounce {
  0%,
  100% {
    transform: translateY(0) rotate(0deg);
  }
  25% {
    transform: translateY(-10px) rotate(-5deg);
  }
  75% {
    transform: translateY(-10px) rotate(5deg);
  }
}

.podium-container {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 16px;
  padding: 20px 0;
}

.podium-place {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  border-radius: 12px;
  position: relative;
  min-width: 100px;
  transition: transform 0.3s ease;
}

.podium-place:hover {
  transform: translateY(-5px);
}

.first {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  order: 2;
  padding-top: 24px;
  box-shadow: 0 8px 24px rgba(255, 215, 0, 0.4);
}

.second {
  background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%);
  order: 1;
  margin-top: 20px;
  box-shadow: 0 6px 20px rgba(192, 192, 192, 0.4);
}

.third {
  background: linear-gradient(135deg, #cd7f32 0%, #e8a87c 100%);
  order: 3;
  margin-top: 30px;
  box-shadow: 0 6px 20px rgba(205, 127, 50, 0.4);
}

.podium-crown {
  font-size: 2rem;
  position: absolute;
  top: -15px;
  animation: crown-float 2s ease-in-out infinite;
}

@keyframes crown-float {
  0%,
  100% {
    transform: translateY(0px) rotate(-5deg);
  }
  50% {
    transform: translateY(-5px) rotate(5deg);
  }
}

.podium-avatar {
  font-size: 2.5rem;
  margin-bottom: 8px;
}

.podium-name {
  font-weight: bold;
  font-size: 0.9rem;
  text-align: center;
  margin-bottom: 4px;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.podium-points {
  font-size: 1.1rem;
  font-weight: bold;
  color: #333;
  margin-bottom: 8px;
}

.podium-rank {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: bold;
  font-size: 0.85rem;
}

.scoreboard-list {
  background: transparent;
}

.scoreboard-item {
  border-radius: 8px;
  margin-bottom: 8px;
  transition: all 0.2s ease;
  border: 2px solid transparent;
}

.scoreboard-item:hover {
  background: rgba(103, 58, 183, 0.05);
  transform: translateX(4px);
}

.rank-first {
  background: linear-gradient(
    90deg,
    rgba(255, 215, 0, 0.1) 0%,
    transparent 100%
  );
  border-left: 4px solid #ffd700;
}

.rank-second {
  background: linear-gradient(
    90deg,
    rgba(192, 192, 192, 0.1) 0%,
    transparent 100%
  );
  border-left: 4px solid #c0c0c0;
}

.rank-third {
  background: linear-gradient(
    90deg,
    rgba(205, 127, 50, 0.1) 0%,
    transparent 100%
  );
  border-left: 4px solid #cd7f32;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  font-size: 0.9rem;
  font-weight: bold;
  background: #e0e0e0;
  color: #666;
}

.badge-gold {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  color: #000;
  box-shadow: 0 2px 8px rgba(255, 215, 0, 0.4);
}

.badge-silver {
  background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%);
  color: #000;
  box-shadow: 0 2px 8px rgba(192, 192, 192, 0.4);
}

.badge-bronze {
  background: linear-gradient(135deg, #cd7f32 0%, #e8a87c 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(205, 127, 50, 0.4);
}

.participant-avatar {
  font-size: 1.5rem;
}
</style>
