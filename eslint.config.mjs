// Tuned eslint — external tooling catches what prose cannot.
// Strict + security-oriented: core rules that catch real defects.
// ponytail: no new deps beyond the TS toolchain in package.json.
export default [
  {
    // Base: globals for Node + ES modules
    files: ["**/*.js", "**/*.mjs", "**/*.ts"],
    ignores: ["node_modules/**", "dist/**", "build/**", ".git/**"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        process: "readonly",
        console: "readonly",
        __dirname: "readonly",
        require: "readonly",
        module: "readonly",
      },
    },
  },
  {
    // Discipline rules for the real code
    files: ["**/*.js", "**/*.mjs", "**/*.ts"],
    rules: {
      "no-unused-vars": "error",
      "no-undef": "error",
      "no-console": ["error", { allow: ["warn", "error"] }],
      "no-debugger": "error",
      "no-constant-condition": "error",
      "no-dupe-keys": "error",
      "no-else-return": "error",
      "no-extra-bind": "error",
      "no-func-assign": "error",
      "no-implied-eval": "error",
      "no-new-func": "error",
      "no-octal": "error",
      "no-redeclare": "error",
      "no-self-assign": "error",
      "no-throw-literal": "error",
      "no-unreachable": "error",
      "no-unneeded-ternary": "error",
      "no-useless-catch": "error",
      "no-useless-escape": "error",
      "prefer-const": "error",
      "prefer-template": "error",
      "no-var": "error",
    },
  },
  {
    // test/ runners are CLI tools — stdout/log is their output channel.
    files: ["test/**/*.js", "test/**/*.mjs"],
    rules: {
      "no-console": "off",
    },
  },
  {
    // Shipped hooks may contain deliberate empty catch blocks (fail-open — a
    // crash in a guard must never block a session). This is intentional, not sin.
    files: ["hooks/**/*.mjs"],
    rules: {
      "no-empty": "off",
    },
  },
]
