<template>
  <div>
    <p v-if="configurations.length === 0">No configurations found.</p>
    <div v-else>
      <div v-for="cfg in configurations" :key="cfg.id" class="configuration">
        <h3>{{ cfg.name }}</h3>
        <p>
          <router-link
            :to="{ name: 'configuration-edit', params: { id: cfg.application, configId: cfg.id } }"
          >
            Edit
          </router-link>
          <button type="button" @click="$emit('delete', cfg.id)">Delete</button>
        </p>
        <div class="settings">
          <div>
            <h4>dev</h4>
            <pre>{{ JSON.stringify(cfg.dev_settings, null, 2) }}</pre>
          </div>
          <div>
            <h4>uat</h4>
            <pre>{{ JSON.stringify(cfg.uat_settings, null, 2) }}</pre>
          </div>
          <div>
            <h4>prod</h4>
            <pre>{{ JSON.stringify(cfg.prod_settings, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "ConfigurationList",
  props: {
    configurations: {
      type: Array,
      required: true,
    },
  },
  emits: ["delete"],
};
</script>

<style scoped>
.configuration {
  border: 1px solid #ccc;
  padding: 1rem;
  margin-bottom: 1rem;
}

.settings {
  display: flex;
  gap: 1rem;
}

.settings > div {
  flex: 1;
}

pre {
  background: #f5f5f5;
  padding: 0.5rem;
  overflow-x: auto;
}
</style>
