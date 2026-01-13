<template>
  <section class="keyword-search">
    <!-- LAYER 1 -->
    <div class="controls">
      <KeywordSearch
        :appid="appid"
        @search="onSearch"
      />
      <div class="divider"></div>
      <KeywordSearchSummary
        v-if="summary"
        :summary="summary"
      />
    </div>

    <!-- LAYER 2 -->
    <ReviewResults
      v-if="keyword"
      :appid="appid"
      :keyword="keyword"
      :initial-reviews="reviews"
      :has-more="hasMore"
      @load-more="loadMore"
    />
  </section>
</template>

<script setup>
import { ref } from "vue";

import KeywordSearch from "@/components/keywordSearch/KeywordSearch.vue";
import KeywordSearchSummary from "@/components/keywordSearch/KeywordSearchSummary.vue";
import ReviewResults from "@/components/keywordSearch/ReviewResults.vue";

const props = defineProps({
  appid: {
    type: Number,
    required: true,
  },
});

const keyword = ref("");
const reviews = ref([]);
const hasMore = ref(false);
//const summary = ref(null);

const summary = ref({
  keyword: "example",
  occurrences: 123,
  reviews_with_keyword: 45,
});


const offset = ref(0);

const limit = 20;

function onSearch(payload) {
  keyword.value = payload.keyword;
  reviews.value = payload.reviews;
  hasMore.value = payload.has_more;
  offset.value = payload.reviews.length;

  summary.value = {
    keyword: payload.keyword,
    occurrences: payload.occurrences,
    reviews_with_keyword: payload.reviews_with_keyword,
  };
}

async function loadMore() {
  const res = await fetch(
    `/api/games/${props.appid}/search_reviews` +
    `?keyword=${encodeURIComponent(keyword.value)}` +
    `&limit=${limit}&offset=${offset.value}`
  );

  const data = await res.json();

  reviews.value.push(...data.reviews);
  offset.value += data.reviews.length;
  hasMore.value = data.has_more;
}
</script>

<style scoped>
.keyword-search {
  margin-top: 1rem;
}

/* Layer 1 */
.controls {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 1.5rem;
  background-color: chocolate;
  min-height: 8rem;
}

/* LEFT SIDE (search) */
.controls> :first-child {
  flex: 6;
}

/* RIGHT SIDE (summary) */
.controls> :last-child {
  flex: 4;
}

.divider {
  width: 1px;
  align-self: stretch;
  /* fills height */
  background-color: black;
}
</style>
