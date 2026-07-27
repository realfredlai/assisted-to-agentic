<template>
  <div>
    <h1>{{ isEdit ? "Edit application" : "New application" }}</h1>
    <p v-if="loading">Loading...</p>
    <form v-else @submit.prevent="handleSubmit">
      <p v-if="generalError">{{ generalError }}</p>

      <div>
        <label for="name">Name</label>
        <input id="name" v-model="name" type="text" />
        <p v-if="fieldErrors.name" class="field-error">{{ fieldErrors.name.join(" ") }}</p>
      </div>

      <div>
        <label for="app_type">Type</label>
        <select id="app_type" v-model="appType">
          <option value="mobile">mobile</option>
          <option value="desktop">desktop</option>
          <option value="web">web</option>
          <option value="cloud">cloud</option>
        </select>
        <p v-if="fieldErrors.app_type" class="field-error">{{ fieldErrors.app_type.join(" ") }}</p>
      </div>

      <div>
        <p>Users</p>
        <div v-for="user in users" :key="user.id">
          <label>
            <input type="checkbox" :value="user.id" v-model="selectedUserIds" />
            {{ user.first_name }} {{ user.last_name }} — {{ user.email }}
          </label>
        </div>
        <p v-if="fieldErrors.users" class="field-error">{{ fieldErrors.users.join(" ") }}</p>
      </div>

      <button type="submit">Save</button>
    </form>
  </div>
</template>

<script>
import api from "../services/api.js";

export default {
  name: "ApplicationFormView",
  data() {
    return {
      name: "",
      appType: "mobile",
      users: [],
      selectedUserIds: [],
      loading: true,
      fieldErrors: {},
      generalError: null,
    };
  },
  computed: {
    isEdit() {
      return !!this.$route.params.id;
    },
  },
  async mounted() {
    try {
      const usersResponse = await api.getUsers();
      this.users = usersResponse.data;

      if (this.isEdit) {
        const appResponse = await api.getApplication(this.$route.params.id);
        this.name = appResponse.data.name;
        this.appType = appResponse.data.app_type;
        this.selectedUserIds = [...appResponse.data.users];
      }
    } catch (err) {
      this.generalError = err.message;
    } finally {
      this.loading = false;
    }
  },
  methods: {
    async handleSubmit() {
      this.fieldErrors = {};
      this.generalError = null;

      const payload = {
        name: this.name,
        app_type: this.appType,
        users: this.selectedUserIds,
      };

      try {
        if (this.isEdit) {
          await api.updateApplication(this.$route.params.id, payload);
        } else {
          await api.createApplication(payload);
        }
        this.$router.push({ name: "applications" });
      } catch (err) {
        const data = err.response?.data;
        if (data && typeof data === "object" && !Array.isArray(data)) {
          this.fieldErrors = data;
          if (data.non_field_errors) {
            this.generalError = data.non_field_errors.join(" ");
          }
        } else {
          this.generalError = err.message;
        }
      }
    },
  },
};
</script>

<style scoped>
.field-error {
  color: #b00020;
  margin: 0.25rem 0 0.75rem;
}
</style>
