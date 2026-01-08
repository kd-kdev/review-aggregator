<template>
    <footer class="flex justify-evenly p-5 bg-green-500">
    <ul>
      <li>
        <router-link :to="{ path: '/about', hash: '#about' }">
          About
        </router-link>
      </li>
      <li>
        <router-link :to="{ path: '/about', hash: '#contact' }">
          Contact
        </router-link>
      </li>
      <li>
        <router-link :to="{ path: '/about', hash: '#privacy' }">
          Privacy
        </router-link>
      </li>
    </ul>
        <div class="text-sm p-1">
        <p>Not affiliated with Steam or Valve. All registered trademarks belong to their respective owners.
             Site made by KD</p>
        </div>
  </footer>
</template>

<script setup></script>

<style scoped>
footer {
    background-color: blueviolet;
}

.p-1 {
    border-top: 1px solid white;
}
</style>