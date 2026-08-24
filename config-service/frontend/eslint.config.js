// ESLint flat config for the Vue SPA. Run via `make lint` from config-service/,
// or `npm run lint` from here. Covers src/ only — build output and node_modules
// are not ours to lint.
import js from "@eslint/js";
import pluginVue from "eslint-plugin-vue";
import globals from "globals";

export default [
  js.configs.recommended,
  ...pluginVue.configs["flat/essential"],
  {
    files: ["**/*.{js,vue}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: { ...globals.browser },
    },
  },
];
