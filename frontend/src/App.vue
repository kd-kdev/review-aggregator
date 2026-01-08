<script setup>
import { ref, onMounted } from 'vue';

const status = ref('loading');

onMounted(async () => {
  const res = await fetch('http://localhost:5000/api/health');
  const data = await res.json();
  status.value = data.status;
});
</script>

<template>
  <div>
    <h1>Backend status:</h1>
    <p>{{ status }}</p>
  </div>
</template>