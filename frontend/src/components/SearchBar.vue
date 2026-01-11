<template>
  <form @submit.prevent="submit">
    <input
      v-model="q"
      placeholder="Search games…"
      aria-label="Search games"
    />
    <button type="submit">Search</button>
  </form>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const q = ref("");

function submit() {
    const value = q.value.trim();
    if (!value) return;

    router.push({
        name: "SearchResults",
        query: { q: value },
    });
}
</script>
