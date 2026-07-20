<template>
  <div>
    <h1>Config Service</h1>
    <p v-if="loading">Loading users...</p>
    <p v-else-if="error">Error loading users: {{ error }}</p>
    <UserList v-else :users="users" />
  </div>
</template>

<script>
import api from "../services/api.js";
import UserList from "../components/UserList.vue";

export default {
  name: "HomeView",
  components: {
    UserList,
  },
  data() {
    return {
      users: [],
      loading: true,
      error: null,
    };
  },
  async mounted() {
    try {
      const response = await api.getUsers();
      this.users = response.data;
    } catch (err) {
      this.error = err.message;
    } finally {
      this.loading = false;
    }
  },
};
</script>