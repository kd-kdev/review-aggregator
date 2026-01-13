<template>
  <div class="review-card">
    <div class="meta">
      <span class="date">
        {{ new Date(review.timestamp_created).toLocaleDateString() }}
      </span>
      <span class="votes">👍 {{ review.votes_up }}</span>
    </div>

    <p class="text">
      {{ review.review }}
    </p>
  </div>
</template>

<script setup>
defineProps({
  review: {
    type: Object,
    required: true,
  },
});
</script>

<style scoped>
.review-card {
  padding: 1rem;
  border-radius: 8px;
  background: #f7f7f7;
  border: 1px solid #e0e0e0;
}

.meta {
  font-size: 0.8rem;
  color: #666;
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.text {
  white-space: pre-wrap;
}
</style>
