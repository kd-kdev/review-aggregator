<template>
  <div class="summary">
    <p>
      Found keyword:
      <strong>{{ summary.keyword }}</strong>
    </p>

    <p>
      Occurrences:
      <strong>{{ summary.occurrences }}</strong>
    </p>

    <p>
      Reviews containing keyword:
      <strong>{{ summary.reviews_with_keyword }}</strong>
    </p>

  </div>
</template>


<script setup>
defineProps({
  summary: {
    type: Object,
    required: true,
  },
});
</script>

<style scoped>
.summary {
  font-size: 0.95rem;
  color: #333;
  padding: 0.75rem 1rem;
  flex-grow: 1;
}

.summary p {
  margin: 0.25rem 0;
}

.placeholder {
  margin-top: 0.75rem;
  padding: 0.5rem;
  background: #e0e0e0;
  border-radius: 4px;
  font-weight: bold;
  text-align: center;
}
</style>
