<template>
  <section class="results">
    <ReviewCard
      v-for="review in reviews"
      :key="review.id"
      :review="review"
    />
  </section>
</template>

<script setup>
import ReviewCard from "./ReviewCard.vue";

defineProps({
  reviews: {
    type: Array,
    required: true,
  },
});
</script>

<style scoped>
.results {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding-bottom: 2rem;
}
</style>
