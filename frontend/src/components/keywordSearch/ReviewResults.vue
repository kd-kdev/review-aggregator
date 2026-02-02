<template>
  <section class="results">
    <div v-if="!reviews || reviews.length === 0" class="no-reviews">
      No reviews found for this keyword.
    </div>

    <ReviewCard
      v-for="review in reviews"
      :key="review.recommendationid"
      :review="review"
      :keyword="selectedKeyword"
    />
  </section>
</template>

<script setup>
import { ref } from "vue";
import ReviewCard from "./ReviewCard.vue";

// reactive selected keyword
const selectedKeyword = ref("");

function onKeywordSelect(keyword) {
  console.log("Keyword selected:", keyword); // will log: "performance"
  selectedKeyword.value = keyword; // now it's just a string
}

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

.no-reviews {
  text-align: center;
  color: #666;
  font-size: 0.95rem;
  padding: 1rem 0;
}
</style>
