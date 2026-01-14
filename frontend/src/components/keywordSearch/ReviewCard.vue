<script setup>
defineProps({
  review: {
    type: Object,
    required: true,
  },
});
</script>

<template>
  <article class="review-card">
    <!-- HEADER -->
    <header class="heading">
      <!-- Thumbs icon -->
      <div class="thumb">
        <img
          src="@/assets/images/icon_thumbsUp.png"
          alt="Recommended"
          class="thumb-img"
        />
      </div>

      <!-- Right side of header -->
      <div class="meta">
        <!-- Row 1 -->
        <div class="row-top">
          <span class="rec-text recommended">
            Recommended
          </span>
        </div>

        <!-- Row 2 -->
        <div class="row-bottom">
          <span class="playtime">
            125.4 hrs on record
          </span>

          <div class="extras">
            <span class="tag">Early Access Review</span>
            <span class="tag">Product received for free</span>

            <a
              class="orig-link"
              href="https://store.steampowered.com"
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
        This game is incredibly relaxing and well designed.
        I’ve spent dozens of hours exploring the world and it
        keeps getting better with every update.

        Highly recommended if you enjoy slow-paced, atmospheric games.
        INSERT READ MORE OPTION IF ABOVE CERTAIN CHAR LENGTH
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
  background-color: goldenrod;
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

/* META container */
.meta {
  flex: 1;
  height: 44px;
  /* SAME as thumb */
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}


/* Row 1: Recommended */
.row-top {
  display: flex;
  align-items: center;
}

/* Row 2: hours left, extras right */
.row-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
}


.row-top,
.row-bottom {
  display: flex;
  align-items: center;
  min-height: 0;
}

/* Hours */
.playtime {
  font-size: 11px;
  color: #666;
}

.rec-text {
  font-size: 1rem;
  /* 16px */
  font-weight: 700;
}

.playtime {
  font-size: 11px;
  line-height: 1.2;
}

/* Tags + link */
.extras {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

/* Modern tag style */
.tag {
  background: #f3f3f3;
  color: #444;
  font-size: 0.75rem;
  padding: 0.05rem 0.45rem;
  border-left: 3px solid #b5b5b5;
}

/* Steam link */
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

/* BODY */
.review-text {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.45;
  font-size: 0.95rem;
  color: #222;
}
</style>
