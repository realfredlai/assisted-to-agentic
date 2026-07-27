<template>
  <div>
    <p v-if="loading">Loading application...</p>
    <p v-else-if="error">Error loading application: {{ error }}</p>
    <div v-else>
      <h1>{{ application.name }}</h1>
      <p>Type: {{ application.app_type }}</p>
      <div>
        <p>Users:</p>
        <p v-if="linkedUsers.length === 0">No users linked.</p>
        <ul v-else>
          <li v-for="user in linkedUsers" :key="user.id">
            {{ user.first_name }} {{ user.last_name }} — {{ user.email }}
          </li>
        </ul>
      </div>

      <p>
        <router-link :to="{ name: 'application-edit', params: { id: application.id } }">
          Edit
        </router-link>
        <router-link :to="{ name: 'applications' }">Back to applications</router-link>
      </p>

      <section>
        <h2>Configurations</h2>
        <p>
          <router-link :to="{ name: 'configuration-new', params: { id: application.id } }">
            New configuration
          </router-link>
        </p>
        <ConfigurationList :configurations="configurations" @delete="handleDelete" />
      </section>
    </div>
  </div>
</template>

<script>
import api from "../services/api.js";
import ConfigurationList from "../components/ConfigurationList.vue";

export default {
  name: "ApplicationDetailView",
  components: {
    ConfigurationList,
  },
  data() {
    return {
      application: null,
      configurations: [],
      users: [],
      loading: true,
      error: null,
    };
  },
  computed: {
    linkedUsers() {
      if (!this.application) {
        return [];
      }
      return this.users.filter((user) => this.application.users.includes(user.id));
    },
  },
  async mounted() {
    await this.fetchAll();
  },
  methods: {
    async fetchAll() {
      this.loading = true;
      this.error = null;
      try {
        const appId = this.$route.params.id;
        const [appResponse, configResponse, usersResponse] = await Promise.all([
          api.getApplication(appId),
          api.getConfigurations(appId),
          api.getUsers(),
        ]);
        this.application = appResponse.data;
        this.configurations = configResponse.data;
        this.users = usersResponse.data;
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },
    async handleDelete(id) {
      if (!window.confirm("Delete this configuration?")) {
        return;
      }
      try {
        await api.deleteConfiguration(this.$route.params.id, id);
        await this.fetchAll();
      } catch (err) {
        this.error = err.message;
      }
    },
  },
};
</script>
