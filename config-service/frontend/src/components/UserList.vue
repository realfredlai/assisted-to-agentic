<template>
  <div>
    <h2>Users</h2>
    <p v-if="users.length === 0">No users found.</p>
    <ul v-else>
      <li v-for="user in users" :key="user.id">
        {{ user.first_name }} {{ user.last_name }} — {{ user.email }}
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: "UserList",
  props: {
    users: {
      type: Array,
      required: true,
    },
  },
};
</script>