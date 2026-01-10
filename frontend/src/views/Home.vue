<template>
<main class="flex-1 p-5 bg-indigo-200 text-left">
    <h1 class="text-2xl font-bold mb-4">Home page</h1>
    <h1>Top Games</h1>

    <p v-if="loading">Loading…</p>
    <p v-else-if="error">{{ error }}</p>

    <!-- 👇 THIS IS THE IMPORTANT PART -->
    <GameOverviewTable
      v-else-if="Array.isArray(games)"
      :games="games"
    />

    <!-- fallback guard -->
    <p v-else>No data</p>
</main>
</template>

<script setup>
import { ref, onMounted } from "vue"
import axios from "axios"
import GameOverviewTable from "@/components/GameOverviewTable.vue"

const games = ref(null)   // 👈 START AS null (important)
const loading = ref(true)
const error = ref(null)

const fetchGamesOverview = async () => {
    try {
        const res = await axios.get("/api/games/overview")

        console.log("API response:", res.data) // 👈 DEBUG LINE

        games.value = res.data.data            // 👈 MUST be array
    } catch (err) {
        console.error(err)
        error.value = "Failed to load games"
    } finally {
        loading.value = false
    }
}

onMounted(fetchGamesOverview)
</script>

<style scoped>
main {
    background-color: antiquewhite;
    min-height: 100vh;
}
</style>