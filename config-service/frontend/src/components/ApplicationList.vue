<template>
  <div>
    <p v-if="applications.length === 0">No applications found.</p>
    <table v-else>
      <thead>
        <tr>
          <th>Name</th>
          <th>Type</th>
          <th>Users</th>
          <th></th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="app in applications" :key="app.id">
          <td>
            <router-link :to="{ name: 'application-detail', params: { id: app.id } }">
              {{ app.name }}
            </router-link>
          </td>
          <td>{{ app.app_type }}</td>
          <td>{{ app.users.length }}</td>
          <td>
            <router-link :to="{ name: 'application-edit', params: { id: app.id } }">
              Edit
            </router-link>
          </td>
          <td>
            <button type="button" @click="$emit('delete', app.id)">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  name: "ApplicationList",
  props: {
    applications: {
      type: Array,
      required: true,
    },
  },
  emits: ["delete"],
};
</script>

<style scoped>
table {
  border-collapse: collapse;
  width: 100%;
}

th,
td {
  border: 1px solid #ccc;
  padding: 0.5rem;
  text-align: left;
}
</style>
