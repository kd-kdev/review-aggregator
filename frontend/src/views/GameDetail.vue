<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import GameReviewSummary from "@/components/GameReviewSummary.vue";
import KeywordSearchLayout from "@/components/keywordSearch/KeywordSearchLayout.vue";


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
    <GameReviewSummary v-if="game" :game="game" />

    <div class="center-steam">
      <iframe
        :src="`https://store.steampowered.com/widget/${appid}/`"
        frameborder="0"
        width="646"
        height="190"
      ></iframe>
    </div>
          <!-- KEYWORD SEARCH -->
      <KeywordSearchLayout :appid="appid" />
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

.center-steam {
  display: flex;
  justify-content: center;
  background: linear-gradient(130deg, #3b4351, #282e39);
  padding: 1rem 0;
}
</style>
