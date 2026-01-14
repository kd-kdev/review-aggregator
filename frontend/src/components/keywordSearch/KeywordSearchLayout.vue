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
    <ReviewFilters />

    <!-- LAYER 2 -->
    <ReviewResults :reviews="reviews" />
    

  </section>
</template>

<script setup>
import { ref } from "vue";

import KeywordSearch from "@/components/keywordSearch/KeywordSearch.vue";
import KeywordSearchSummary from "@/components/keywordSearch/KeywordSearchSummary.vue";
import ReviewResults from "@/components/keywordSearch/ReviewResults.vue";
import ReviewFilters from "./ReviewFilters.vue";

const props = defineProps({
  appid: {
    type: Number,
    required: true,
  },
});

const keyword = ref("");
//const reviews = ref([]);
const hasMore = ref(false);
//const summary = ref(null);

// SUMMARY PLACEHOLDER VALUE FOR TESTING
const summary = ref({
  keyword: "example",
  occurrences: 123,
  reviews_with_keyword: 45,
});

// REVIEWS FOR TESTING UI
const reviews = ref([
  {
    id: 1,
    author: "User123",
    text: "This game is amazing and relaxing",
    recommended: true,
  },
  {
    id: 2,
    author: "User456",
    text: "Too grindy for my taste",
    recommended: false,
  },
  {
    id: 3,
    author: "User456",
    text: "Too grindy for my taste",
    recommended: false,
  },
  {
    id: 1,
    author: "User123",
    text: "This game is amazing and relaxing",
    recommended: true,
  },
  {
    id: 2,
    author: "User456",
    text: "Too grindy for my taste",
    recommended: false,
  },
  {
    id: 3,
    author: "User456",
    text: "Too grindy for my taste",
    recommended: false,
  },
  {
    id: 1,
    author: "User123",
    text: "This game is amazing and relaxing",
    recommended: true,
  },
  {
    id: 2,
    author: "User456",
    text: "Too grindy for my taste",
    recommended: false,
  },
  {
    id: 3,
    author: "User456",
    text: "Too grindy for my taste",
    recommended: false,
  },
]);



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
