#!/usr/bin/env node
// one-man test runner — drives the assert-based guard self-checks.
// No framework: each test_*.py exits 0 on pass, 1 on fail.
// Runs every test_*.py in hooks/ via the system python.
// Usage: node test/run-tests.js   (or `pnpm test`)
import { execSync } from "node:child_process"
import { readdirSync } from "node:fs"
import { join, dirname } from "node:path"
import { fileURLToPath } from "node:url"

const root = join(dirname(fileURLToPath(import.meta.url)), "..")
const hooksDir = join(root, "hooks")
const py = process.platform === "win32" ? "python" : process.env.PYTHON || "python3"

// Top-level test_*.py + hooks/lib/test_*.py (shared helpers get tested too)
const top = readdirSync(hooksDir).filter((f) => f.startsWith("test_") && f.endsWith(".py"))
const lib = readdirSync(join(hooksDir, "lib")).filter((f) => f.startsWith("test_") && f.endsWith(".py"))
const scriptTests = ["../scripts/test_check_lessons.py", "../scripts/test_lessons_seed.py", "../scripts/ci-lessons-fixture.py", "../scripts/test_validate_policies.py", "../scripts/test_drift_check.py", "../scripts/test_promote.py"]
const tests = [...top, ...lib.map((f) => join("lib", f)), ...scriptTests]
if (!tests.length) {
  console.error("no test_*.py found in hooks/")
  process.exit(1)
}

let failed = 0
for (const t of tests) {
  try {
    execSync(`"${py}" "${join(hooksDir, t)}"`, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] })
    console.log(`PASS ${t}`)
  } catch (e) {
    failed++
    console.error(`FAIL ${t}\n${e.stderr || e.stdout || e.message}`)
  }
}

if (failed) {
  console.error(`\n${failed}/${tests.length} hook self-checks FAILED`)
  process.exit(1)
}
console.log(`\n${tests.length}/${tests.length} hook self-checks passed`)
