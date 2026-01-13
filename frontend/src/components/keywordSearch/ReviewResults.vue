<template>
  <section class="results">
    <ReviewCard
      v-for="r in reviews"
      :key="r.recommendationid"
      :review="r"
    />

    <button v-if="hasMore" @click="$emit('load-more')">
      Load more
    </button>
  </section>
</template>

<script setup>
defineProps({
  reviews: Array,
  hasMore: Boolean,
});
</script>

<style scoped>
.results {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>
