<template>
  <header class="app-header">
    <router-link to="/" class="logo">
      <img src="@/assets/images/temp-logo.png" alt="Logo" />
    </router-link>

    <div class="search">
      Search bar pending
    </div>
  </header>
</template>

<script setup></script>

<style scoped>
.app-header {
    display: flex;
    align-items: center;
    /* vertical alignment */
    justify-content: space-between;
    /* left & right */
    padding: 0 1rem;
    background-color: aquamarine;
}


.search {
    margin-left: auto;
    /* optional with space-between */
}
</style>