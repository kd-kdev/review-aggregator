<template>
  <section class="keyword-search">
    <!-- LAYER 1: Search + Summary -->
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

    <!-- Optional Filters -->
    <ReviewFilters />

    <!-- LAYER 2: Review Results -->
    <ReviewResults
      :reviews="reviews"
      :selected-keyword="keyword"
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
import ReviewFilters from "./ReviewFilters.vue";

const props = defineProps({
  appid: {
    type: Number,
    required: true,
  },
});

const keyword = ref("");
const reviews = ref([]);
const hasMore = ref(false);
const summary = ref(null);

const offset = ref(0);
const limit = 20;

/**
 * Maps backend review objects to the shape expected by ReviewCard.vue
 */
function mapBackendReviews(rawReviews) {
  return rawReviews.map((r) => ({
    id: r.recommendationid,
    author: r.steamid ? `User ${r.steamid}` : "Unknown",
    text: r.review,
    recommended: r.voted_up,

    // Use the new backend keys
    playtime_minutes: r.playtime_minutes ?? null,
    playtime_at_review_minutes: r.playtime_at_review_minutes ?? null,

    steam_purchase: r.steam_purchase,
    written_during_early_access: r.written_during_early_access,
    steam_link: `https://store.steampowered.com/app/${r.appid}`,
  }));
}

/**
 * Called when user performs a keyword search
 */
async function onSearch(payload) {
  keyword.value = payload.keyword;
  offset.value = 0;

  try {
    const res = await fetch(
      `/api/games/${props.appid}/reviews/keyword?keyword=${encodeURIComponent(
        keyword.value
      )}&limit=${limit}&offset=${offset.value}`
    );
    const data = await res.json();

    reviews.value = mapBackendReviews(data.reviews);
    hasMore.value = data.has_more;
    offset.value = reviews.value.length;

    summary.value = data.summary;
  } catch (err) {
    console.error("Failed to fetch reviews:", err);
  }
}

/**
 * Called when user clicks "Load more"
 */
async function loadMore() {
  try {
    const res = await fetch(
      `/api/games/${props.appid}/reviews/keyword?keyword=${encodeURIComponent(
        keyword.value
      )}&limit=${limit}&offset=${offset.value}`
    );
    const data = await res.json();

    reviews.value.push(...mapBackendReviews(data.reviews));
    offset.value += data.reviews.length;
    hasMore.value = data.has_more;
  } catch (err) {
    console.error("Failed to load more reviews:", err);
  }
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
