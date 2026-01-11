<template>
  <header class="app-header">
    <router-link to="/" class="logo">
      <img src="@/assets/images/temp-logo.png" alt="Logo" />
    </router-link>

    <div class="search">
      <SearchBar />
    </div>
  </header>
</template>

<script setup>
import SearchBar from "@/components/SearchBar.vue";
</script>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1rem;
  background-color: aquamarine;
}

.search {
  margin-left: auto;
}
</style>
