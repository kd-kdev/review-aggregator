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
        <th>Game</th>
        <th>Total Reviews</th>
        <th>Positive %</th>
        <th>Negative %</th>
      </tr>
    </thead>

    <tbody>
      <tr v-for="game in games" :key="game.appid">
        <td>{{ game.name }}</td>
        <td>{{ game.total_reviews }}</td>
        <td>{{ game.positive_pct }}%</td>
        <td>{{ game.negative_pct }}%</td>
      </tr>
    </tbody>
  </table>
</template>
