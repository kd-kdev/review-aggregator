<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const appid = route.params.appid;

const game = ref(null);
const loading = ref(true);
const error = ref(null);

onMounted(async () => {
  try {
    const res = await fetch(`/api/games/${appid}`);

    if (!res.ok) {
      if (res.status === 404) {
        throw new Error("Game not found");
      }
      throw new Error("Failed to load game");
    }

    game.value = await res.json();
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <main>
    <div class="game-detail">
      <div v-if="loading">Loading…</div>

      <div v-else-if="error">
        <p class="error">{{ error }}</p>
      </div>

      <div v-else>
        <img
          v-if="game.capsule_image_v5"
          :src="game.capsule_image_v5"
          alt="Game capsule"
          class="capsule"
        />

        <h1>{{ game.name }}</h1>

        <p v-if="game.release_date">
          Released:
          {{ new Date(game.release_date).toLocaleDateString() }}
        </p>

        <p v-if="game.review_score_desc">
          <strong>Review score:</strong> {{ game.review_score_desc }}
        </p>
      </div>
    </div>
  </main>
</template>

<style scoped>
main {
  background-color: antiquewhite;
  min-height: 100vh;
}

.game-detail {
  max-width: 900px;
  padding: 1rem;
}

.capsule {
  max-width: 300px;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.error {
  color: red;
}
</style>
