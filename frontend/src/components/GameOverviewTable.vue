<script setup>
defineProps({
    games: {
        type: Array,
        required: true,
    },
})
</script>

<template>
  <table>
    <thead>
      <tr>
        <th>Title</th>
        <th>Total Reviews</th>
        <th>Positive %</th>
        <th>Negative %</th>
      </tr>
    </thead>

    <tbody>
      <tr v-for="game in games" :key="game.appid">
                <td class="game-cell">
        <img
            v-if="game.capsule_image"
            :src="game.capsule_image"
            :alt="game.name"
            class="capsule"
        />
        <span class="game-name">
            <router-link :to="`/games/${game.appid}`">
                {{ game.name }}
            </router-link>
        </span>
        </td>

        <td>{{ game.total_reviews }}</td>
        <td>{{ game.positive_pct }}%</td>
        <td>{{ game.negative_pct }}%</td>
      </tr>
    </tbody>
  </table>
</template>

<style scoped>
.game-cell {
    display: flex;
    align-items: center;
    gap: 12px;
}

.capsule {
    width: 92px;
    /* Steam-like mini capsule */
    height: auto;
    border-radius: 4px;
    object-fit: cover;
}

.game-name {
    font-weight: 500;
    line-height: 1.2;
}

/* Table style */
table {
    width: 100%;
    border-collapse: collapse;
}

thead th {
    border-bottom: 0.125rem solid #e5e7eb;
    /* 2px */
    padding: 0.75rem 0.5rem;
    text-align: left;
    font-weight: 600;
    font-size: 0.875rem;
    color: #374151;
}

tbody td {
    padding: 0.875rem 0.5rem;
    font-size: 0.875rem;
}

th:first-child,
td:first-child {
    padding-right: 1rem;
    /* 48px */
    text-align: left;
}

th:not(:first-child),
td:not(:first-child) {
    text-align: center;
}

tbody tr:not(:last-child) td {
    border-bottom: 0.0625rem solid #f0f0f0;
    /* 1px */
}

tbody tr:hover {
    background-color: #fafafa;
}
</style>