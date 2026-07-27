import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import ApplicationListView from "../views/ApplicationListView.vue";
import ApplicationFormView from "../views/ApplicationFormView.vue";
import ApplicationDetailView from "../views/ApplicationDetailView.vue";
import ConfigurationFormView from "../views/ConfigurationFormView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "home",
      component: HomeView,
    },
    {
      path: "/applications",
      name: "applications",
      component: ApplicationListView,
    },
    {
      path: "/applications/new",
      name: "application-new",
      component: ApplicationFormView,
    },
    {
      path: "/applications/:id",
      name: "application-detail",
      component: ApplicationDetailView,
    },
    {
      path: "/applications/:id/edit",
      name: "application-edit",
      component: ApplicationFormView,
    },
    {
      path: "/applications/:id/configurations/new",
      name: "configuration-new",
      component: ConfigurationFormView,
    },
    {
      path: "/applications/:id/configurations/:configId/edit",
      name: "configuration-edit",
      component: ConfigurationFormView,
    },
  ],
});

export default router;
