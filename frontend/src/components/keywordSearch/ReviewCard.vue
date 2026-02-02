<script setup>
import { ref, computed } from "vue";

const props = defineProps({
  review: {
    type: Object,
    required: true,
  },
  keyword: {
    type: String,
    default: "",
  },
});

// Recommended / Not Recommended
const isRecommended = computed(() => !!props.review.recommended);
const recText = computed(() => (isRecommended.value ? "Recommended" : "Not Recommended"));

// Playtime display (optional)
const playtime = computed(() =>
  props.review.playtime && props.review.playtime !== "N/A"
    ? `${props.review.playtime} hrs on record`
    : ""
);

// Tags (handle nulls safely)
const tags = computed(() => {
  const t = [];
  if (props.review.written_during_early_access) t.push("Early Access Review");
  if (props.review.received_for_free) t.push("Product received for free");
  return t;
});

// Steam link
const steamUrl = computed(() =>
  props.review.steam_link ||
  (props.review.steamid && props.review.recommendationid
    ? `https://steamcommunity.com/profiles/${props.review.steamid}/recommended/${props.review.recommendationid}`
    : "https://store.steampowered.com")
);

// Read More functionality
const maxLength = 300; // characters before "Read More"
const expanded = ref(false);

const truncatedText = computed(() => {
  const text = props.review.text || "";
  return text.length > maxLength && !expanded.value
    ? text.slice(0, maxLength) + "..."
    : text;
});

function toggleReadMore() {
  expanded.value = !expanded.value;
}

const highlightedText = computed(() => {
  if (!props.review.text) return "";

  const safeKeyword = props.keyword?.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  if (!safeKeyword) return truncatedText.value;

  const regex = new RegExp(`(${safeKeyword})`, "gi");

  return truncatedText.value.replace(regex, '<mark>$1</mark>');
});


</script>

<template>
  <article class="review-card">
    <!-- HEADER -->
    <header class="heading">
      <div class="thumb">
        <img
          src="@/assets/images/icon_thumbsUp.png"
          :alt="recText"
          class="thumb-img"
        />
      </div>

      <div class="meta">
        <!-- Row 1 -->
        <div class="row-top">
          <span class="rec-text" :class="{ recommended: isRecommended }">
            {{ recText }}
          </span>
        </div>

        <!-- Row 2 -->
        <div class="row-bottom">
          <span class="playtime">{{ playtime }}</span>

          <div class="extras">
            <span v-for="(tag, idx) in tags" :key="idx" class="tag">
              {{ tag }}
            </span>

            <a
              class="orig-link"
              :href="steamUrl"
              target="_blank"
              rel="noopener noreferrer"
              title="View on Steam"
            >
              <svg viewBox="0 0 24 24" class="ext-icon">
                <path
                  d="M14 3h7v7h-2V6.4l-9.3 9.3-1.4-1.4L17.6 5H14V3zM5 5h6v2H7v10h10v-4h2v6H5V5z"
                />
              </svg>
            </a>
          </div>
        </div>
      </div>
    </header>

    <!-- BODY -->
    <div class="body">
      <p class="review-text">
        <span v-html="highlightedText"></span>
        <button
          v-if="props.review.text && props.review.text.length > maxLength"
          class="read-more-btn"
          @click="toggleReadMore"
        >
          {{ expanded ? "Collapse" : "Read More" }}
        </button>
      </p>
    </div>
  </article>
</template>

<style scoped>
.review-card {
  padding: 1rem;
  border-radius: 1rem;
  margin: 0 2rem;
  background: #ffffff;
  border: 1px solid #e6e6e6;
  box-shadow: 0 1px 0 rgba(0, 0, 0, 0.02);
}

/* HEADER */
.heading {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 0.75rem;
}

.thumb {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
}

.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.meta {
  flex: 1;
  height: 44px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.row-top {
  display: flex;
  align-items: center;
}

.row-top .recommended {
  color: #1a7f37;
}

.row-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.playtime {
  font-size: 11px;
  color: #666;
  line-height: 1.2;
}

.rec-text {
  font-size: 1rem;
  font-weight: 700;
}

.extras {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.tag {
  background: #f3f3f3;
  color: #444;
  font-size: 0.75rem;
  padding: 0.05rem 0.45rem;
  border-left: 3px solid #b5b5b5;
}

.orig-link {
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

.orig-link:hover {
  color: #000;
}

.ext-icon {
  width: 16px;
  height: 16px;
  fill: currentColor;
}

.review-text {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.45;
  font-size: 0.95rem;
  color: #222;
}

/* Read more button */
.read-more-btn {
  background: none;
  border: none;
  color: #1a7f37;
  font-size: 0.85rem;
  cursor: pointer;
  margin-left: 0.25rem;
  padding: 0;
}

.read-more-btn:hover {
  text-decoration: underline;
}

.highlight {
  background-color: orange;
  color: #000;
  /* optional: make text readable */
  padding: 0 2px;
  border-radius: 2px;
}
</style>
