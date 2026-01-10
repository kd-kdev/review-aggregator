<template>
<main class="flex-1 p-5 bg-indigo-200 text-left">
    <h1>Top Games</h1>

    <p v-if="loading">Loading…</p>
    <p v-else-if="error">{{ error }}</p>

    <GameOverviewTable
      v-else-if="Array.isArray(games)"
      :games="games"
    />

    <!-- fallback guard -->
    <p v-else>No data</p>

    <h1>Funny reviews section</h1>
    <p>hand picked (for now ?) funny reviews</p>
    <p>placeholder</p>

    <h1>SteamReviews+ in numbers:</h1>
    <p>how many games in database, reviews total, analysis etc.</p>
    <p>placeholder</p>
</main>
</template>

<script setup>
import { ref, onMounted } from "vue"
import axios from "axios"
import GameOverviewTable from "@/components/GameOverviewTable.vue"

const games = ref(null)
const loading = ref(true)
const error = ref(null)

const fetchGamesOverview = async () => {
    try {
        const res = await axios.get("/api/games/overview")

        console.log("API response:", res.data)

        games.value = res.data.data
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