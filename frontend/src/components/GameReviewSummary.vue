<script setup>
import { computed } from "vue";

const props = defineProps({
  game: {
    type: Object,
    required: true,
  },
});

const totalReviews = computed(() => props.game.total_reviews ?? 0);
const positive = computed(() => props.game.total_positive ?? 0);
const negative = computed(() => props.game.total_negative ?? 0);

const positivePct = computed(() =>
  totalReviews.value
    ? ((positive.value / totalReviews.value) * 100).toFixed(1)
    : "0.0"
);

const negativePct = computed(() =>
  totalReviews.value
    ? ((negative.value / totalReviews.value) * 100).toFixed(1)
    : "0.0"
);

const reviewScoreDesc = computed(
  () => props.game.review_score_desc ?? null
);
</script>

<template>
  <section class="review-summary">
    <img
      v-if="game.capsule_image_v5"
      :src="game.capsule_image_v5"
      alt="Game capsule"
      class="capsule"
    />

    <div class="info">
      <h2>{{ game.name }}</h2>

      <p v-if="reviewScoreDesc" class="score-desc">
        {{ reviewScoreDesc }}
      </p>

      <div class="stats">
        <span class="total">
          Total reviews:
          <strong>{{ totalReviews.toLocaleString() }}</strong>
        </span>

        <span class="divider"> · </span>

        <span class="positive">
          Positive:
          <strong>{{ positive.toLocaleString() }}</strong>
          ({{ positivePct }}%)
        </span>

        <span class="divider"> · </span>

        <span class="negative">
          Negative:
          <strong>{{ negative.toLocaleString() }}</strong>
          ({{ negativePct }}%)
        </span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.score-desc {
  font-weight: 600;
  color: #444;
}

.review-summary {
  display: flex;
  gap: 1.5rem;
  align-items: center;
  padding: 1rem;
  border-radius: 8px;
  background-color: #f4f4f4;
}

.capsule {
  width: 188px;
  border-radius: 6px;
}

.info h2 {
  margin: 0 0 0.25rem;
}

.total {
  margin-bottom: 0.75rem;
}

.breakdown p {
  margin: 0.25rem 0;
}

.positive {
  color: #1a7f37;
}

.negative {
  color: #b42318;
}
</style>