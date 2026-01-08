<template>
    <div class="d-flex justify-center">
        <div class="max-w-xl w-100">
            <Header />

            <main>
                <router-view />
            </main>

            <Footer />
        </div>
    </div>
</template>

<script setup>
import Header from '@/components/Header.vue'
import Footer from '@/components/Footer.vue'
</script>

<style scoped>
.d-flex {
    background-color: #2d2d2d;
}
</style>