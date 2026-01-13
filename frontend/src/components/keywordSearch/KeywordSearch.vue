<template>
  <div class="keyword-search">
    <!-- Line 1 -->
    <label class="title">
      Search for keywords in reviews:
    </label>

    <!-- Line 2 -->
    <div class="inputs">
      <input
        v-model="keyword"
        type="text"
        placeholder="Enter a keyword…"
        @keyup.enter="submit"
      />

      <span class="or">or use a preset</span>

      <select v-model="keyword" @change="submit">
        <option disabled value="">Select a keyword</option>
        <option
          v-for="preset in presets"
          :key="preset"
          :value="preset"
        >
          {{ preset }}
        </option>
      </select>
    </div>
  </div>
</template>


<script setup>
import { ref } from "vue";

const emit = defineEmits(["search"]);

const keyword = ref("");

const presets = [
  "performance",
  "crash",
  "multiplayer",
  "controller",
  "bugs",
  "graphics",
];

function submit() {
  if (!keyword.value) return;

  emit("search", {
    keyword: keyword.value.trim(),
  });
}
</script>


<style scoped>
.keyword-search {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-left: 1rem;
}

.title {
  font-weight: 600;
  font-size: 0.95rem;
}

.inputs {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

input,
select {
  padding: 0.45rem 0.6rem;
  border-radius: 4px;
  border: 1px solid #ccc;
  font-size: 1rem;
}

input {
  width: 200px;
}

select {
  min-width: 160px;
}

.or {
  font-size: 0.85rem;
}
</style>

