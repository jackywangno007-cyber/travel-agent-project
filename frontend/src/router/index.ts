import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/Home.vue";
import Result from "../views/Result.vue";
import DayDetail from "../views/DayDetail.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "Home",
      component: Home,
    },
    {
      path: "/result",
      name: "Result",
      component: Result,
    },
    {
      path: "/trip/day/:dayIndex",
      name: "DayDetail",
      component: DayDetail,
      props: true,
    },
  ],
});

export default router;
