# One Man v1.5.0 Independent Engineering Assessment

You are assessing two related but separate systems:

1. My current local Claude Code environment
2. The One Man repository, currently at version 1.4.0

Do not begin implementing changes.

Your task is to inspect, understand, test, challenge, and assess the current system before recommending what One Man v1.5.0 should become.

## Context

I am a vibe coder.

I can define product goals, expected outcomes, constraints, and quality standards, but I cannot reliably detect every software engineering, security, architectural, testing, operational, or workflow mistake myself.

I already use plugins, skills, agents, hooks, rules, commands, MCP tools, documentation, tests, and other development tooling systematically.

However, merely installing or documenting these capabilities does not guarantee that an AI coding agent will actually use them.

An AI can still:

* skip required analysis
* ignore project rules
* bypass tests
* perform shallow reviews
* claim success without evidence
* make unplanned architectural changes
* overfit to the immediate task
* introduce technical debt
* miss edge cases
* weaken security
* generate AI slop
* complete only the happy path
* leave unfinished integration work
* silently ignore available tools or skills
* produce work that appears complete but is not production-ready

One Man exists to solve that problem.

It should provide a portable, reusable, privacy-conscious engineering environment that helps a solo vibe coder produce work closer to the standards of an excellent engineering organization.

My local Claude Code environment may contain personal configuration, credentials, provider details, local paths, memories, project history, or device-specific data. One Man should let me reproduce the useful engineering system on another device without blindly copying sensitive or personal data.

## Core Question

Does my current local Claude Code environment and One Man v1.4.0 genuinely provide a complete, enforced, evidence-driven engineering harness?

Or does it mostly provide tools, instructions, and good intentions that an AI agent can still bypass?

Assess whether the system truly helps a solo vibe coder operate with the combined discipline expected from:

* a strong product team
* a senior software engineer
* a software architect
* a quality engineer
* a security engineer
* a performance engineer
* a release engineer
* a site reliability engineer
* a platform engineer
* a developer-experience engineer
* a responsible offensive-security practitioner
* a technical lead
* an engineering manager
* a high-performing software organization

Do not interpret “top” as adding maximum complexity, maximum tooling, or enterprise ceremony.

The target is the strongest practical system appropriate for a solo developer using AI heavily.

The system should be rigorous where rigor prevents real mistakes, lightweight where ceremony adds little value, and adaptive to the project’s actual risk.

---

# Assessment Principles

## 1. Inspect reality, not documentation

Do not assume a capability exists because it is mentioned in:

* README files
* CLAUDE.md
* configuration files
* prompts
* skill descriptions
* plugin lists
* comments
* roadmap documents
* previous release notes

Verify whether it is:

* installed
* configured
* reachable
* invoked
* enforced
* tested
* observable
* portable
* maintainable
* functioning correctly

Clearly distinguish among:

1. Claimed capability
2. Installed capability
3. Configured capability
4. Available capability
5. Automatically invoked capability
6. Enforced capability
7. Verified capability
8. Production-ready capability

## 2. Distinguish guidance from enforcement

Classify every important rule or control as one of the following:

* Informational only
* Recommended
* Convention-based
* Prompt-enforced
* Workflow-enforced
* Tool-enforced
* Hook-enforced
* Test-enforced
* CI-enforced
* Permission-enforced
* Architecturally impossible to bypass

For every critical control, explain how an AI could currently skip or bypass it.

## 3. Require evidence

Do not accept phrases such as:

* “should work”
* “appears correct”
* “likely covered”
* “tests exist”
* “the agent is instructed to”
* “the plugin handles this”

Use concrete evidence such as:

* executed commands
* configuration resolution
* hook execution
* test results
* failure-path tests
* observed tool calls
* generated artifacts
* blocked invalid operations
* reproducible setup
* CI behavior
* logs
* traces
* permission boundaries
* clean-device installation results

## 4. Avoid both underengineering and overengineering

Identify:

* missing controls that create real quality or safety risk
* duplicated tools
* conflicting rules
* overlapping plugins
* unnecessary complexity
* slow or expensive workflows
* excessive token use
* controls that create ceremony without meaningful protection
* mechanisms that are too rigid for small projects
* mechanisms that are too weak for high-risk projects

Every recommendation must be proportional to risk and usefulness.

## 5. Preserve privacy and portability

One Man must separate reusable engineering infrastructure from personal state.

Assess whether it properly separates:

### Portable and reusable

* generic engineering rules
* workflow definitions
* hooks
* validation logic
* test harnesses
* reusable skills
* project templates
* safe defaults
* command definitions
* documentation structures
* policy schemas
* quality gates

### Personal or device-specific

* API keys
* credentials
* tokens
* account identifiers
* private provider endpoints
* local absolute paths
* machine-specific binaries
* personal memories
* private project history
* shell history
* SSH material
* local caches
* user-specific model mappings
* private environment variables
* sensitive logs

Determine whether One Man can be installed on another device without transferring unnecessary personal data.

---

# Part A: Understand the Existing System

Inspect the repository and the active local Claude Code environment.

Build a factual system map covering:

* repository structure
* current version
* installation flow
* update flow
* configuration flow
* Claude Code integration
* global configuration
* project-level configuration
* plugins
* skills
* agents and subagents
* hooks
* slash commands
* MCP servers
* local tools
* external tools
* permissions
* environment variables
* secrets handling
* templates
* policies
* tests
* CI
* logging
* observability
* release process
* documentation
* migration behavior
* uninstall or cleanup behavior
* portability behavior
* operating-system assumptions

For each component, record:

* purpose
* source of truth
* owner
* activation condition
* dependencies
* failure behavior
* bypass possibility
* test coverage
* portability implications
* whether it contains personal data

Identify contradictions between global Claude Code behavior and One Man-managed behavior.

---

# Part B: Evaluate the Engineering Lifecycle

Determine whether the current system supports and enforces the complete software lifecycle.

## 1. Discovery and product definition

Assess support for:

* problem definition
* user needs
* scope
* constraints
* assumptions
* feasibility
* success criteria
* acceptance criteria
* non-goals
* product requirements
* technical requirements
* risk classification
* project-specific definition of done

Check whether the AI is required to understand the problem before editing code.

## 2. Repository reconnaissance

Assess whether the AI must first inspect:

* repository structure
* architecture
* existing conventions
* active branch
* working-tree state
* relevant documentation
* tests
* dependencies
* build system
* recent changes
* unresolved work
* known risks
* generated files
* ownership boundaries

Check whether it can begin editing based only on the user’s latest message.

## 3. Planning and decomposition

Assess support for:

* task classification
* risk classification
* dependency analysis
* milestone planning
* incremental delivery
* sequencing
* rollback planning
* validation planning
* explicit assumptions
* unresolved questions
* stop conditions
* scope control

Determine whether plans are required only when useful, rather than produced as empty ceremony.

## 4. Architecture and design

Assess support for:

* domain modeling
* data modeling
* API design
* module boundaries
* dependency direction
* state management
* concurrency
* failure modes
* recovery
* security boundaries
* performance constraints
* compatibility
* migrations
* extensibility
* operational behavior
* architecture decision records
* trade-off analysis

Check whether significant architectural decisions require explicit reasoning and documentation.

## 5. Implementation discipline

Assess whether the system enforces:

* minimal justified change
* consistency with local conventions
* clear naming
* maintainable abstractions
* bounded complexity
* dead-code avoidance
* duplication control
* dependency discipline
* deterministic behavior
* defensive input handling
* error propagation
* cancellation and timeout handling
* resource cleanup
* backwards compatibility
* migration safety
* documentation updates
* no placeholder implementations
* no silent TODO completion claims
* no unrelated rewrites

## 6. Refactoring discipline

Determine whether the system distinguishes:

* cleanup
* refactor
* restructure
* redesign
* re-architecture
* rewrite
* migration
* modernization
* optimization
* consolidation

For refactoring specifically, check whether it requires:

* preserved observable behavior
* characterization tests where behavior is unclear
* baseline tests before changes
* incremental transformations
* no hidden feature changes
* performance comparison where relevant
* compatibility verification
* rollback capability
* removal of temporary compatibility layers
* proof that duplication or complexity was genuinely reduced

Check whether “refactor” can currently become an uncontrolled rewrite.

## 7. Verification and testing

Assess support and enforcement for:

* formatting
* linting
* type checking
* compilation
* unit tests
* integration tests
* contract tests
* end-to-end tests
* regression tests
* smoke tests
* property-based tests
* fuzz tests
* mutation testing where justified
* compatibility tests
* migration tests
* failure-path tests
* concurrency tests
* accessibility tests
* manual validation
* acceptance testing

Determine whether the system selects tests based on project type and risk.

Check whether agents can claim completion after running only a narrow targeted test.

## 8. Security engineering

Assess:

* threat modeling
* trust boundaries
* authentication
* authorization
* secret handling
* input validation
* output encoding
* dependency vulnerabilities
* supply-chain risk
* command injection
* path traversal
* deserialization
* SSRF
* XSS
* CSRF
* SQL injection
* privilege boundaries
* filesystem permissions
* sandboxing
* sensitive logging
* privacy
* secure defaults
* abuse cases
* rate limiting
* denial-of-service resistance
* cryptographic usage
* incident readiness

Evaluate security testing only within authorized, defensive, and project-relevant boundaries.

Check whether high-risk changes trigger stronger review and validation automatically.

## 9. Performance and efficiency

Assess support for:

* baseline measurement
* profiling
* benchmarking
* latency
* throughput
* memory
* CPU
* disk usage
* network usage
* startup time
* build time
* token usage
* AI context usage
* caching
* algorithmic complexity
* resource leaks
* performance regressions
* cost constraints

Check whether optimization requires measurement rather than intuition.

## 10. Review quality

Assess whether review is:

* independent from implementation
* evidence-based
* adversarial where useful
* scoped to the actual diff
* aware of requirements
* aware of architecture
* aware of security
* aware of performance
* aware of tests
* capable of rejecting incomplete work

Check for self-review bias when the same AI implements and approves its own work.

## 11. Release engineering

Assess:

* semantic versioning
* changelog generation
* release notes
* artifact building
* artifact verification
* reproducible builds
* checksums or signatures where appropriate
* dependency locking
* release gates
* version consistency
* migration notes
* rollback
* staged rollout
* installation testing
* upgrade testing
* downgrade behavior
* clean-device verification

## 12. Operations and maintenance

Assess:

* logging
* metrics
* tracing
* health checks
* diagnostics
* error reporting
* alerts
* incident response
* root-cause analysis
* postmortems
* backup and restore
* disaster recovery
* supportability
* deprecation
* technical-debt tracking
* ownership
* documentation freshness

Adapt this category to local and CLI software rather than assuming a cloud service.

---

# Part C: Evaluate the AI Engineering Harness

This is the most important section.

Determine whether One Man currently behaves like a real harness or merely a collection of instructions and tools.

Assess the following:

## Task lifecycle

Can every meaningful task be tracked through states such as:

* received
* understood
* classified
* scoped
* planned
* approved when necessary
* in progress
* implemented
* validated
* reviewed
* blocked
* completed
* released
* monitored

Is there durable evidence of these transitions?

## Policy resolution

Determine:

* where rules come from
* precedence between global and project rules
* how conflicts are resolved
* whether the effective policy can be displayed
* whether rules are versioned
* whether policy changes are auditable
* whether stale rules can remain active
* whether agents know which rules applied to a task

## Tool and skill invocation

Determine whether relevant tools and skills are:

* merely installed
* suggested by prompts
* selected automatically
* required by task classification
* verified as executed
* allowed to fail silently
* replaceable by weaker manual behavior

Check whether the harness can prove that a required skill, plugin, agent, or validation step actually ran.

## Gate enforcement

Assess whether work can proceed when:

* the repository is dirty
* requirements are unclear
* the task exceeds scope
* tests are already failing
* security checks fail
* implementation adds undocumented dependencies
* generated code is incomplete
* review finds unresolved defects
* release checks fail
* personal secrets are detected
* unsupported assumptions are made

For every gate, test whether it truly blocks progress or only prints a warning.

## Completion claims

Determine whether “done” requires evidence such as:

* changed files
* satisfied acceptance criteria
* test results
* review findings
* unresolved risks
* documentation updates
* release impact
* manual verification
* known limitations

Check whether the AI can say “completed” while leaving skipped checks or hidden failures.

## Agent delegation

Assess:

* when subagents are useful
* whether subagents inherit required context
* whether they receive bounded tasks
* whether their work is verified
* whether multiple agents duplicate effort
* whether review agents are independent
* whether delegation wastes tokens
* whether the main agent improperly trusts summaries
* whether critical evidence is lost during delegation

## Context management

Assess:

* context gathering
* context compression
* stale context
* conflicting context
* cross-session continuity
* project isolation
* personal-data leakage
* retrieval quality
* prompt injection risks
* excessive file reading
* insufficient code understanding

## Anti-slop protections

Determine whether the system detects or prevents:

* fake completeness
* placeholder code
* shallow wrappers
* duplicated abstractions
* untested happy paths
* invented APIs
* ignored return values
* broad exception swallowing
* meaningless tests
* tests that assert implementation details only
* unverifiable claims
* excessive comments
* generic AI-style documentation
* unnecessary files
* premature abstractions
* dependency bloat
* configuration bloat
* excessive agent spawning
* performative planning
* accidental scope expansion

---

# Part D: Portability and Clean-Device Reproduction

Determine whether One Man can reproduce the useful local engineering environment on another device.

Assess the complete lifecycle:

1. Fresh device or clean user profile
2. Prerequisite detection
3. Installation
4. Configuration
5. Safe import of non-sensitive preferences
6. Explicit secret setup
7. Plugin and skill installation
8. Hook installation
9. MCP configuration
10. Validation
11. Health check
12. Update
13. Repair
14. Reset
15. Uninstall
16. Data cleanup

Check for:

* hardcoded paths
* operating-system assumptions
* missing prerequisites
* undocumented manual steps
* non-idempotent installation
* duplicate configuration
* stale state
* partial failures
* unsafe overwrites
* secrets copied into the repository
* personal data included in exports
* inability to explain what will be installed
* inability to preview changes
* inability to roll back
* inability to verify effective configuration

Define what a safe portable profile should and should not contain.

---

# Part E: Adversarial and Failure Testing

Do not assess only the intended workflow.

Try to determine what happens when:

* the AI ignores a rule
* a hook fails
* a plugin is missing
* an MCP server is unavailable
* a skill produces invalid output
* a required command times out
* tests already fail before work starts
* the repository contains unrelated changes
* the current branch is wrong
* credentials are missing
* credentials are accidentally present in files
* configuration is malformed
* multiple rules conflict
* the AI attempts to skip review
* the AI marks skipped tests as passed
* a subagent hallucinates completion
* installation is interrupted halfway
* an update runs over a customized setup
* a device has a different OS
* the repository is offline
* dependencies cannot be downloaded
* the user requests an unsafe shortcut
* the task is tiny and the full workflow would be wasteful
* the task is high-risk and the default workflow is insufficient

Identify fail-open behavior.

Critical quality and security controls should generally fail closed unless there is an explicit, visible, auditable override.

---

# Part F: Benchmark Against High-Performing Engineering Practice

Evaluate the system against the practical capabilities of excellent engineering organizations.

Do not copy enterprise processes blindly.

For each area, classify One Man as:

* Missing
* Ad hoc
* Documented
* Partially automated
* Automated
* Enforced
* Verified
* Excessive for the project’s needs

Areas to assess:

* product discovery
* requirements engineering
* technical design
* architecture governance
* implementation discipline
* code review
* testing
* security
* privacy
* performance
* accessibility
* dependency management
* supply-chain security
* release engineering
* observability
* incident readiness
* technical-debt management
* documentation
* developer experience
* reproducibility
* portability
* policy enforcement
* auditability
* AI-agent governance
* cost and token efficiency

The goal is not to claim that One Man equals a large company.

The goal is to determine whether it gives one person the highest practical coverage achievable through good automation, strong defaults, evidence, and enforced workflows.

---

# Required Findings

Explicitly identify:

1. What is genuinely strong today
2. What only appears strong on paper
3. What is installed but unused
4. What is used but unenforced
5. What is enforced but unverified
6. What can be bypassed
7. What is duplicated
8. What conflicts
9. What is too expensive or slow
10. What risks personal-data leakage
11. What breaks portability
12. What creates false confidence
13. What is missing for v1.5.0
14. What should not be added
15. What should be simplified or removed

---

# Proposed v1.5.0 Plan

After completing the assessment, propose a focused One Man v1.5.0 plan.

Do not assume v1.5.0 needs major new features.

The correct outcome may be:

* strengthening enforcement
* consolidating existing capabilities
* removing duplication
* adding evidence capture
* improving policy resolution
* fixing portability
* improving clean-device setup
* hardening privacy boundaries
* adding failure-path tests
* improving observability
* introducing risk-adaptive gates
* making completion claims verifiable

For every proposed milestone include:

* problem
* evidence
* user impact
* current bypass
* proposed control
* enforcement layer
* files or systems likely affected
* dependencies
* security implications
* privacy implications
* portability implications
* testing strategy
* acceptance criteria
* rollback strategy
* expected complexity
* token and runtime cost
* reason it belongs in v1.5.0

Separate recommendations into:

### Must have

Required to prevent false confidence, unsafe behavior, broken portability, or major quality failures.

### Should have

Strong improvements that meaningfully improve reliability or usability.

### Could have

Useful but nonessential improvements.

### Reject or defer

Ideas that are overengineered, duplicative, immature, too expensive, or unrelated to the v1.5.0 purpose.

---

# Required Output Structure

Produce the assessment in this exact order:

## 1. Executive verdict

State clearly:

* whether One Man v1.4.0 is currently a real engineering harness
* whether enforcement is meaningful
* whether it is safe and portable
* whether it is ready to serve as the foundation for v1.5.0
* the highest-risk gaps

Do not soften the verdict.

## 2. System map

Describe the current local Claude Code and One Man architecture.

## 3. Capability inventory

Provide a table with:

| Capability | Claimed | Installed | Active | Enforced | Verified | Portable | Evidence | Gap |

## 4. Workflow coverage matrix

Provide a matrix covering the complete engineering lifecycle.

## 5. Enforcement matrix

For every critical rule, show:

| Rule or control | Current mechanism | Bypass method | Failure mode | Required enforcement |

## 6. Privacy and portability assessment

Explain exactly what is safe to reproduce and what must remain device-local.

## 7. Adversarial findings

Describe realistic ways the AI, tooling, installer, or user could bypass the intended system.

## 8. Duplication and complexity findings

Identify unnecessary tools, conflicts, repeated rules, or excessive ceremony.

## 9. Top-quality benchmark

Compare the system with the practical standards expected from a high-performing engineering organization.

## 10. v1.5.0 recommendation

Provide the proposed scope, milestones, gates, and acceptance criteria.

## 11. Deferred work

Separate future improvements from v1.5.0.

## 12. Final scorecard

Score each area from 0 to 5:

* Product discipline
* Requirements discipline
* Architecture
* Implementation quality
* Refactoring safety
* Testing
* Security
* Performance
* Review independence
* Release engineering
* Operations
* Documentation
* Developer experience
* AI-agent enforcement
* Evidence and auditability
* Privacy
* Portability
* Maintainability
* Cost efficiency
* Overall confidence

Use this scale:

* 0: absent
* 1: mostly manual or unreliable
* 2: partially implemented
* 3: functional but bypassable
* 4: strongly enforced and tested
* 5: exceptional, evidence-backed, and difficult to bypass

For every score below 4, state what prevents it from reaching 4.

---

# Working Rules

* Do not modify code during this assessment.
* Do not create commits.
* Do not open a pull request.
* Do not change global Claude Code configuration.
* Do not expose credentials or secret values.
* Redact sensitive data in all output.
* Do not assume an installed tool is working.
* Do not trust previous assessment documents without revalidation.
* Run safe read-only checks where possible.
* Ask for access only when a required area genuinely cannot be inspected.
* Clearly mark anything that could not be verified.
* Separate facts, observations, inferences, risks, and recommendations.
* Prefer direct evidence over optimistic interpretation.
* Challenge the design rather than trying to please me.
* Do not recommend complexity merely because large companies use it.
* Do not claim “top quality” unless the evidence supports it.

The final result should tell me whether One Man is truly becoming an enforceable engineering operating system for a solo AI-assisted developer, or whether it is still mainly a well-organized collection of prompts, plugins, and conventions.
