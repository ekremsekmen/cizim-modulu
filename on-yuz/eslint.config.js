//  ESLint — hata yakalayan kurallar:  TypeScript, React kancalarının kuralları
//  ( bağımlılık listesi, render sırasında yan etki, ref ) .  Biçim kuralı yok.
import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "node_modules"] },
  {
    files: ["**/*.{ts,tsx}"],
    extends: [js.configs.recommended, ...tseslint.configs.recommended, reactHooks.configs.flat["recommended-latest"]],
    languageOptions: { ecmaVersion: 2022, globals: globals.browser },
    rules: {
      "react-hooks/exhaustive-deps": "error",
      "@typescript-eslint/no-unused-vars": ["error", { varsIgnorePattern: "^_", argsIgnorePattern: "^_" }],
    },
  },
);
