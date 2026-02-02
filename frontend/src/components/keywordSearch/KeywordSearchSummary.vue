<template>
  <div class="summary">
    <p>
      Found keyword:
      <strong>{{ summary?.keyword || "—" }}</strong>
    </p>

    <p>
      Occurrences:
      <strong>{{ summary?.occurrences ?? "—" }}</strong>
    </p>

    <p>
      Reviews containing keyword:
      <strong>{{ summary?.reviews_with_keyword ?? "—" }}</strong>
    </p>

  </div>
</template>

<script setup>
defineProps({
  summary: {
    type: Object,
    default: null, // allow null when no search has been done yet
  },
});
</script>

<style scoped>
.summary {
  font-size: 0.95rem;
  color: #333;
  padding: 0.75rem 1rem;
  flex-grow: 1;

  /* keeps panel visible even before search */
  border-radius: 6px;
  min-height: 4rem;
  /* prevent collapsing */
}

.summary p {
  margin: 0.25rem 0;
}
</style>