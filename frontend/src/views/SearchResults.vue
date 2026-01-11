<template>
  <div>
    <h1>Search results for "{{ q }}"</h1>

    <div v-if="loading">Loading…</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <GameOverviewTable :games="games" />
      <button v-if="hasMore" @click="loadMore">Load more</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";
import { useRoute } from "vue-router";
import GameOverviewTable from "@/components/GameOverviewTable.vue";

const route = useRoute();
const q = ref(route.query.q || "");
const limit = ref(20);
const offset = ref(0);

const games = ref([]);
const loading = ref(false);
const error = ref(null);
const hasMore = ref(false);

async function fetchResults(reset = false) {
  if (!q.value) {
    games.value = [];
    return;
  }
  loading.value = true;
  error.value = null;
  try {
    if (reset) {
      offset.value = 0;
      games.value = [];
    }
    const res = await fetch(`/api/games/search?q=${encodeURIComponent(q.value)}&limit=${limit.value}&offset=${offset.value}`);
    if (!res.ok) throw new Error("Search failed");
    const payload = await res.json();
    games.value.push(...payload.data);
    // simple hasMore heuristic:
    hasMore.value = payload.data.length === limit.value;
    offset.value += payload.data.length;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

onMounted(() => fetchResults(true));
watch(() => route.query.q, (newQ) => {
  q.value = newQ;
  fetchResults(true);
});

function loadMore() {
  fetchResults(false);
}
</script>

<style scoped>
main {
  background-color: antiquewhite;
  min-height: 100vh;
}
</style>