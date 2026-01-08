<template>
<main class="flex-1 p-5 bg-indigo-200 text-left">
    <h1 class="text-2xl font-bold mb-4">Home page</h1>
    <h1>Backend status:</h1>
    <p>{{ status }}</p>
</main>
</template>

<script scoped>
import { ref, onMounted } from 'vue';

const status = ref('loading');

onMounted(async () => {
    const res = await fetch('http://localhost:5000/api/health');
    const data = await res.json();
    status.value = data.status;
});
</script>

<style scoped>
main {
    background-color: antiquewhite;
    min-height: 100vh;
}
</style>