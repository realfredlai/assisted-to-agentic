<template>
  <div>
    <h1>Applications</h1>
    <p><router-link :to="{ name: 'application-new' }">New application</router-link></p>
    <p v-if="loading">Loading applications...</p>
    <p v-else-if="error">Error loading applications: {{ error }}</p>
    <ApplicationList v-else :applications="applications" @delete="handleDelete" />
  </div>
</template>

<script>
import api from "../services/api.js";
import ApplicationList from "../components/ApplicationList.vue";

export default {
  name: "ApplicationListView",
  components: {
    ApplicationList,
  },
  data() {
    return {
      applications: [],
      loading: true,
      error: null,
    };
  },
  async mounted() {
    await this.fetchApplications();
  },
  methods: {
    async fetchApplications() {
      this.loading = true;
      this.error = null;
      try {
        const response = await api.getApplications();
        this.applications = response.data;
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },
    async handleDelete(id) {
      if (!window.confirm("Delete this application?")) {
        return;
      }
      try {
        await api.deleteApplication(id);
        await this.fetchApplications();
      } catch (err) {
        this.error = err.message;
      }
    },
  },
};
</script>
