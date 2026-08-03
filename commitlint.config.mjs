export default {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "type-enum": [
      2,
      "always",
      ["feat", "fix", "refactor", "test", "docs", "chore", "build", "ci", "style", "revert"],
    ],
    "subject-case": [0], // allow "fix: thing" lowercase — matches one-man commit style
    "type-case": [2, "always", "lower-case"],
    "footer-leading-blank": [0], // Co-Authored-By footer is conventionally attached directly
  },
}
