<template>
  <div id="app">
    <nav>
      <router-link to="/">Users</router-link>
      <router-link to="/applications">Applications</router-link>
    </nav>
    <router-view />
  </div>
</template>

<script>
export default {
  name: "App",
};
</script>

<style scoped>
nav {
  padding: 1rem;
}

nav a {
  margin-right: 1rem;
}
</style>