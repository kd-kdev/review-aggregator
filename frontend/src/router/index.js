import { createRouter, createWebHistory } from "vue-router";
import DefaultLayout from "@/layouts/DefaultLayout.vue";
import Home from "@/views/Home.vue";
import About from "@/views/About.vue";
import GameDetail from "@/views/GameDetail.vue";

const routes = [
  {
    path: "/",
    component: DefaultLayout,
    children: [
      {
        path: "",
        name: "Home",
        component: Home,
      },
      {
        path: "about",
        name: "About",
        component: About,
      },
      {
        path: "games/:appid/",
        name: "GameDetail",
        component: GameDetail,
        props: true,
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to) {
    if (to.hash) {
      return { el: to.hash, behavior: "smooth" };
    }
    return { top: 0 };
  },
});

/**
 * Enforce trailing slash for game pages
 */
router.beforeEach((to, from, next) => {
  if (to.name === "GameDetail" && !to.path.endsWith("/")) {
    next({ path: `${to.path}/`, replace: true });
  } else {
    next();
  }
});

export default router;
