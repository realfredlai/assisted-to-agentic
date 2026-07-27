<template>
  <div>
    <h1>{{ isEdit ? "Edit configuration" : "New configuration" }}</h1>
    <p v-if="loading">Loading...</p>
    <form v-else @submit.prevent="handleSubmit">
      <p v-if="generalError">{{ generalError }}</p>

      <div>
        <label for="name">Name</label>
        <input id="name" v-model="name" type="text" />
        <p v-if="fieldErrors.name" class="field-error">{{ fieldErrors.name.join(" ") }}</p>
      </div>

      <div>
        <label for="dev_settings">Dev settings (JSON)</label>
        <textarea id="dev_settings" v-model="devSettingsText" rows="6"></textarea>
        <p v-if="jsonErrors.dev_settings" class="field-error">{{ jsonErrors.dev_settings }}</p>
        <p v-else-if="fieldErrors.dev_settings" class="field-error">
          {{ fieldErrors.dev_settings.join(" ") }}
        </p>
      </div>

      <div>
        <label for="uat_settings">UAT settings (JSON)</label>
        <textarea id="uat_settings" v-model="uatSettingsText" rows="6"></textarea>
        <p v-if="jsonErrors.uat_settings" class="field-error">{{ jsonErrors.uat_settings }}</p>
        <p v-else-if="fieldErrors.uat_settings" class="field-error">
          {{ fieldErrors.uat_settings.join(" ") }}
        </p>
      </div>

      <div>
        <label for="prod_settings">Prod settings (JSON)</label>
        <textarea id="prod_settings" v-model="prodSettingsText" rows="6"></textarea>
        <p v-if="jsonErrors.prod_settings" class="field-error">{{ jsonErrors.prod_settings }}</p>
        <p v-else-if="fieldErrors.prod_settings" class="field-error">
          {{ fieldErrors.prod_settings.join(" ") }}
        </p>
      </div>

      <button type="submit">Save</button>
    </form>
  </div>
</template>

<script>
import api from "../services/api.js";
import { extractApiErrors } from "../services/apiErrors.js";

const SETTINGS_FIELDS = ["dev_settings", "uat_settings", "prod_settings"];

export default {
  name: "ConfigurationFormView",
  data() {
    return {
      name: "",
      devSettingsText: "{}",
      uatSettingsText: "{}",
      prodSettingsText: "{}",
      loading: true,
      fieldErrors: {},
      jsonErrors: {},
      generalError: null,
    };
  },
  computed: {
    isEdit() {
      return !!this.$route.params.configId;
    },
  },
  async mounted() {
    if (this.isEdit) {
      try {
        const response = await api.getConfiguration(
          this.$route.params.id,
          this.$route.params.configId
        );
        this.name = response.data.name;
        this.devSettingsText = JSON.stringify(response.data.dev_settings, null, 2);
        this.uatSettingsText = JSON.stringify(response.data.uat_settings, null, 2);
        this.prodSettingsText = JSON.stringify(response.data.prod_settings, null, 2);
      } catch (err) {
        this.generalError = err.message;
      }
    }
    this.loading = false;
  },
  methods: {
    parseSettings(text) {
      let parsed;
      try {
        parsed = JSON.parse(text);
      } catch (e) {
        return { error: "Invalid JSON" };
      }
      if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
        return { error: "Must be a JSON object" };
      }
      return { value: parsed };
    },
    async handleSubmit() {
      this.fieldErrors = {};
      this.generalError = null;
      this.jsonErrors = {};

      const textByField = {
        dev_settings: this.devSettingsText,
        uat_settings: this.uatSettingsText,
        prod_settings: this.prodSettingsText,
      };

      const parsedByField = {};
      let hasJsonError = false;
      for (const field of SETTINGS_FIELDS) {
        const result = this.parseSettings(textByField[field]);
        if (result.error) {
          this.jsonErrors[field] = result.error;
          hasJsonError = true;
        } else {
          parsedByField[field] = result.value;
        }
      }

      if (hasJsonError) {
        return;
      }

      const payload = {
        name: this.name,
        dev_settings: parsedByField.dev_settings,
        uat_settings: parsedByField.uat_settings,
        prod_settings: parsedByField.prod_settings,
      };

      const appId = this.$route.params.id;

      try {
        if (this.isEdit) {
          await api.updateConfiguration(appId, this.$route.params.configId, payload);
        } else {
          await api.createConfiguration(appId, payload);
        }
        this.$router.push({ name: "application-detail", params: { id: appId } });
      } catch (err) {
        const { fieldErrors, generalError } = extractApiErrors(err);
        this.fieldErrors = fieldErrors;
        this.generalError = generalError;
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

textarea {
  width: 100%;
  font-family: monospace;
}
</style>
