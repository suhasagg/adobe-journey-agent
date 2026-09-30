# Adobe Journey Agent 

## Architecture

```text
Conversational goal
 -> API / verified identity
 -> four-layer memory recall
 -> LangGraph planner
 -> typed journey DAG
 -> deterministic policy
 -> specialist agents
      Inventory
      Analysis
      Design
      Simulation
      Optimization
      Channel
      Guardrails
      Publish
 -> HITL for writes
 -> AJO adapter
 -> Adobe Journey Optimizer
 -> audit/evaluation/memory
```

## Why this is not a single prompt

A production journey system is a distributed workflow engine containing probabilistic reasoning.
LLMs are appropriate for intent decomposition, design assistance, explanation and evidence-bound
recommendations. They are not the authority for permissions, consent, frequency limits, idempotency,
publication or external transaction state.

## Code map

`api.py` is ingress. `graph.py` is the workflow control plane. `planner.py` creates a typed DAG.
`models.py` defines contracts. `agents/` contains eight executable specialist capabilities. `ajo/`
isolates Adobe HTTP contracts. `security/` owns deterministic permission decisions. `memory/` owns
working, episodic, semantic and procedural memory.

## LangGraph

The state machine is `recall -> plan -> execute -> approval? -> finish`. `StateGraph` makes legal
transitions explicit. The reference uses `MemorySaver` for local execution; production needs a
durable checkpoint store. Checkpoint state and semantic memory are different: checkpoints answer
"where is this workflow?" while semantic memory answers "what durable knowledge is relevant?"

## LangChain

The model factory centralizes provider choice. Structured Pydantic output is used for `Plan` and
`JourneySpec`, preventing arbitrary prose from becoming executable control state.

## Journey representation

`JourneySpec` contains entry criteria, typed nodes, edges, exit criteria and KPIs. A journey is
naturally a directed state machine:

```text
ENTRY
 -> eligibility
 -> consent
 -> channel/action
 -> WAIT
 -> condition
    | yes -> conversion
    | no  -> alternate action
 -> frequency check
 -> EXIT
```

Production validation must detect unreachable nodes, cycles that violate policy, missing exits,
invalid wait durations, unsupported actions and ambiguous physical identifiers.

## Specialist agents

### InventoryAgent
Discovers journey definitions through the repository. At scale use pagination, metadata indexing and
server-side filtering rather than loading all journeys into model context.

### AnalyzeAgent
Interprets verified evidence for drop-offs, branch behavior, conversion, latency and channel
performance. It is instructed not to invent metrics. SQL/analytics systems calculate; the LLM
explains.

### DesignAgent
Produces a typed multi-step `JourneySpec`: entry, conditions, actions, waits, exits and KPIs. Unknown
resource IDs must remain unresolved until deterministic catalog resolution.

### SimulationAgent
The included deterministic simulator validates structure and reports the supplied sample population.
It deliberately does not fabricate conversion outcomes. Production simulation requires authoritative
profile/event distributions or a calibrated behavioral model.

### OptimizeAgent
Reasons about drop-off, channel effectiveness, waits, fatigue, consent, conversion, holdouts and
measurement from supplied evidence. Recommendations are not silently deployed.

### ChannelAgent
Chooses channel/action strategy from eligibility, consent and preference evidence, including fallback
and suppression. Consent is never inferred from a language model.

### GuardrailAgent
Represents deterministic journey constraints such as consent requirement, frequency cap, quiet hours
and maximum duration. In production these rules belong in a policy service with versioning.

### PublishAgent
The only write capability. It requires Manage-Journeys authorization plus approval before calling the
AJO repository. This implements: **model proposes -> validator checks -> policy authorizes -> human
approves -> idempotent adapter commits**.

## All four memory layers

**Working memory:** recent conversation/current plan/tool evidence. Bounded and short-lived.
Production: Redis + TTL.

**Episodic memory:** previous journey runs, actions, outcomes and failures. Useful for "what happened
last time?" Production: PostgreSQL/event log.

**Semantic memory:** durable governed facts such as approved channel rules, terminology or customer
journey definitions. Production: embeddings + hybrid BM25/vector retrieval with ACLs.

**Procedural memory:** reusable playbooks, for example `analyze -> design -> simulate -> guardrail ->
review -> publish`. Procedures must be versioned and evaluated; historical success is not sufficient
to promote a procedure to trusted policy.

Memory pipeline:
```text
interaction -> secret/PII filter -> classify -> provenance -> dedupe -> store/TTL
 -> ACL retrieval -> lexical/vector fusion -> rerank -> context budget -> model
```

## Memory poisoning

CRM fields, documents, tool output and historical memory are untrusted data. They cannot change
system policy, tenant, permissions, tool allowlists or approval requirements. Store provenance,
authority, confidence and validity periods.

## Planner / DAG

Each step has ID, capability, objective, dependencies and write classification. Validate uniqueness,
dependency existence, acyclicity, maximum depth/size, capability allowlist, risk and cost budget.
Dynamic replanning should create an immutable new plan version rather than silently rewriting history.

## Parallel execution

Compute a ready set of dependency-satisfied tasks and execute independent reads concurrently under
global, tenant, model-provider and AJO semaphores. Unbounded agent fan-out is a resource-exhaustion
bug, not intelligence.

## Identity and permissions

Production derives identity/tenant/permissions from verified OIDC/JWT or service identity, never from
request-body claims. Reads and writes require separate entitlements. Service-account capability must
not be confused with caller authorization (confused-deputy defense).

## Consent, frequency and quiet hours

These are deterministic business constraints. A channel action is eligible only if all required
consent/policy predicates pass. Frequency caps require an authoritative contact-history counter.
Quiet hours require recipient-local time and policy, not server time.

## Channel arbitration

A production channel decision can score:
`eligibility + consent + preference + reachability + fatigue + predicted utility + cost`.
Hard policy predicates are evaluated before scoring. A high predicted conversion cannot override
lack of consent.

## Simulation

Three levels:
1. structural: graph validity/reachability;
2. replay: historical event/profile replay;
3. probabilistic: calibrated behavioral model/Monte Carlo.

Simulation outputs need assumptions, population/time window, model version, confidence and
limitations. Never present a language-model guess as a simulation.

## Optimization

Optimization should be constrained:
```text
maximize expected business utility
subject to consent, frequency, budget, fairness/governance, channel capacity and experience quality
```
Use controlled experiments/holdouts for causal claims. Observational conversion differences do not
automatically prove a journey change caused improvement.

## Experimentation

Journey optimization should integrate hypotheses, randomization unit, primary/guardrail metrics,
power/MDE, SRM checks, stopping rule, novelty/seasonality and multiple-testing controls. Statistical
computation belongs in deterministic analytics libraries/services.

## AJO adapter

`AJOClient` centralizes authorization, API key, IMS organization, sandbox, timeout and retry.
`JourneyRepository` provides a stable domain interface. Verify current licensed Journey Optimizer
endpoint/payload contracts before enabling production mutations; do not guess private or changing
Adobe service contracts.

## HITL transaction

Correct approval:
1. persist canonical journey proposal;
2. hash payload;
3. checkpoint;
4. authenticate approver;
5. verify permission/resource scope;
6. show exact intended effect;
7. record decision/reason/time;
8. ensure payload hash unchanged;
9. resume;
10. commit idempotently;
11. record external ID and audit.

Changing the proposal invalidates approval.

## Idempotency

Persist `(tenant, operation, key, request_hash, state, external_resource_id)`. If POST succeeds but
the network times out, reconcile rather than blindly retry. Exactly-once distributed execution is
generally unrealistic; target at-least-once delivery with idempotent effects.

## Sagas

A journey may depend on audience, content, channel configuration and experiment resources. Model
cross-system work as a saga with compensations where possible. Mark irreversible operations and
place approval before them.

## Reliability

Classify validation, authorization, policy, rate-limit, network, model, permanent external,
ambiguous-commit, approval-timeout and dependency failures. Retry only transient classes with
exponential backoff+jitter, deadlines, circuit breakers and rate limits.

## Security

Threats: prompt injection, malicious content, tool abuse, confused deputy, cross-tenant leakage,
memory poisoning, data exfiltration, secret leakage and dependency compromise. Controls: typed
allowlisted tools, deterministic policy, RBAC/ABAC, workload identity, egress restrictions, DLP,
tenant partitioning, encryption, audit, signed artifacts/SBOM and HITL.

## Privacy/governance

Journey orchestration may touch profile and behavioral data. Apply purpose limitation, consent,
minimization, labels, residency, retention/deletion, legal hold and provider data-processing rules.
Prefer evidence references/aggregates over raw unnecessary PII in prompts.

## Observability

Trace:
```text
journey.run
 +- memory.recall
 +- planner
 +- analyze/design/simulate/optimize
 +- guardrails
 +- publish
     +- policy
     +- approval
     +- ajo.http
 +- memory.write
```
Metrics: task/run success, p50/p95/p99, model latency/tokens, AJO error/429, retries, approval wait,
simulation calibration, policy blocks, groundedness, experiment quality and cost per successful goal.
Never log secrets or unrestricted customer profiles.

## Evaluation

Unit-test graph validation, policies, caps and memory isolation. Contract-test Adobe adapters.
Maintain golden sets for routing/planning/tool selection. Test prompt injection, poisoned memory,
cross-tenant attempts and privilege escalation. Chaos-test timeout, 429, partial commit and DB
failover. Evaluate trajectories, not merely final prose.

## Scaling topology

```text
API Gateway
    |
Orchestrator API ---- Checkpoint/Postgres
    |
 Queue/Event Bus
    |
 +-- interactive workers
 +-- simulation workers
 +-- memory consolidation workers
 +-- monitoring/anomaly workers
    |
 Tool/AJO Gateway
    |
 Adobe Journey Optimizer
```

Use Redis for ephemeral state/rate limiting, Postgres for workflows/approvals/idempotency/outbox,
vector storage for semantic memory, object storage for artifacts and a warehouse/lake for historical
analytics/evaluation. Partition and quota by tenant.

## Context engineering

Priority: immutable policy -> exact task -> authoritative evidence -> relevant high-trust memory ->
compact prior results. Unlimited transcript accumulation is not memory architecture.

## Multi-model routing

Use small models for classification/extraction, stronger reasoning for complex design/optimization,
dedicated embeddings for retrieval and deterministic engines for statistics/simulation/policy.
Model/provider routing belongs behind `llm.py`.

## Continuous optimization

Always-on analysis should be event-driven:
`journey telemetry -> stream -> anomaly/metric worker -> evidence packet -> agent recommendation ->
experiment/approval`. Do not keep an LLM process continuously polling.

## Deployment

Docker runs non-root. Kubernetes baseline is intentionally small. Production adds HPA, PDB, topology
spread, NetworkPolicy, workload identity, external secrets, TLS/WAF, read-only FS, graceful drain,
multi-AZ stores and separate interactive/background pools.

## CI/CD

`lint/type -> unit -> dependency/SAST/secret scan -> AJO contracts -> agent golden eval ->
adversarial eval -> image/SBOM/sign -> staging -> shadow/canary -> progressive rollout`.
Prompts, policies, models and retrieval changes are versioned release artifacts.

## DR

Protect checkpoint, idempotency and approval state. If workflow state is lost while Adobe resources
survive, replay can duplicate side effects. Recovery reconciles external IDs before resumption.
Define separate RPO/RTO for workflow, audit, memory and analytics.

## Capacity planning

Model requests/sec, steps/run, model calls/step, token sizes, AJO latency/quota, concurrent journeys,
simulation workload, event volume and tenant skew. Approval waiters should consume durable storage,
not worker threads.

## Cost engineering

Measure total cost per successful journey objective: model + retrieval + stores + simulation +
Adobe/tool calls + retries + observability + human review. Optimize through model routing, context
compression, caching and asynchronous batching without weakening policy.

## Questions

**Why specialist agents?** Smaller capability, permission and evaluation surfaces.
**Why graph orchestration?** Explicit state, dependency, resumption and failure boundaries.
**Why deterministic guardrails?** Consent and policy cannot depend on probabilistic compliance.
**Why simulate separately from design?** Proposal generation and outcome estimation have different
evidence and validation requirements.
**Why four memories?** Different trust/retention/retrieval semantics.
**How prevent duplicate publication?** Idempotency + external reconciliation.
**How handle partial failure?** durable state + classified retry + saga compensation.
**How scale?** stateless ingress + durable state + queues + bounded workers + partitioned stores.

## Production gap checklist

Before a real Journey Optimizer tenant: verified identity, durable LangGraph checkpointer, persistent
four-layer memory, authenticated approval/resume, idempotency/outbox/reconciliation, authoritative
resource/schema catalogs, full consent/contact-history service, production simulation/analytics,
verified current Adobe contracts, OpenTelemetry, DLP, tenant quotas, load/chaos/adversarial tests,
multi-AZ/DR and incident kill switches.

## Mental model

```text
CUSTOMER-JOURNEY INTENT
 -> IDENTITY/TENANT
 -> MEMORY
 -> TYPED PLANNER
 -> JOURNEY DAG
 -> SPECIALIST AGENTS
 -> AUTHORITATIVE EVIDENCE
 -> JOURNEY STATE-MACHINE SPEC
 -> SIMULATION
 -> POLICY/GUARDRAILS
 -> HUMAN APPROVAL
 -> IDEMPOTENT AJO COMMIT
 -> TELEMETRY
 -> ANALYSIS/EXPERIMENT
 -> MEMORY + EVALUATION
```

Journey Agent is best understood as a **policy-governed distributed state-machine
authoring and optimization platform containing probabilistic reasoning components**.

# PART II — CODE & SYSTEM DESIGN HANDBOOK

## 34. Every source module and its architectural responsibility

```text
src/journey_agent/
  api.py                  HTTP ingress; run/thread creation
  graph.py                LangGraph state machine and task scheduler
  planner.py              natural-language goal -> typed capability DAG
  models.py               contracts: Principal, Step, Plan, JourneySpec, State
  llm.py                  centralized model-provider seam
  config.py               environment/config boundary
  agents/
    inventory.py          journey discovery
    analyze.py            evidence-grounded journey analysis
    design.py             typed journey state-machine design
    simulate.py           deterministic simulation boundary
    optimize.py           evidence-grounded optimization
    channel.py            channel/action recommendation
    guardrails.py         deterministic policy constraints
    publish.py            controlled external write
    registry.py           closed capability allowlist
  ajo/
    client.py             Adobe HTTP/auth/sandbox boundary
    repository.py         domain-facing journey persistence interface
  memory/
    store.py              runnable working + long-term memory backend
    manager.py            memory taxonomy/lifecycle facade
  security/
    policy.py             read/write authorization + approval classification
```

A key Principal-level separation is:

```text
LLM reasoning ≠ authorization ≠ validation ≠ external transaction
```

Those concerns must remain independently testable.

## 35. End-to-end request trace

Request:

> "Analyze our onboarding journey, identify where customers drop, redesign it for email + push,
> simulate the new flow, optimize waits and publish only after I approve."

A reasonable plan is:

```text
S1 inventory
      |
S2 analyze
      |
 +----+---------+
 |              |
S3 design    S4 channel
 |              |
 +------+- ------+
        |
   S5 guardrails
        |
   S6 simulate
        |
   S7 optimize
        |
   S8 publish [WRITE]
```

Runtime:

```text
API
 -> verified principal
 -> memory recall
 -> typed planner
 -> DAG validation
 -> ready-set scheduler
 -> capability agents
 -> journey specification
 -> guardrail validation
 -> simulation/evidence
 -> publish proposal
 -> durable approval
 -> idempotency
 -> AJO adapter
 -> external resource
 -> audit + memory + evaluation
```

The orchestration layer—not individual agents—owns the global workflow.

## 36. `api.py`: production ingress

The sample accepts principal data in the request to remain runnable. A production API must derive
identity and tenant from verified OIDC/JWT or workload identity.

Recommended ingress:

```text
Internet/enterprise client
 -> WAF/API gateway
 -> TLS
 -> JWT signature/issuer/audience verification
 -> tenant mapping
 -> request quota
 -> deadline/correlation ID
 -> Journey Agent API
```

Never let the LLM choose tenant, role or sandbox.

`run_id` identifies an execution. `thread_id` identifies conversational continuity. An approval,
idempotency record and audit event should reference run/step IDs explicitly.

## 37. `models.py`: executable contracts

`Step.capability` is a closed enum. This converts an open-ended language problem into a bounded
capability problem.

`JourneySpec` models the journey as nodes and edges rather than prose. Production types should add:
- node schema version;
- channel/action resource references;
- wait semantics;
- condition AST;
- consent requirements;
- retry/error transitions;
- ownership;
- labels;
- deployment environment.

Schema-version every durable object because workflows can survive application deployments.

## 38. Journey as a state machine

A journey is a directed graph:

```text
ENTRY
  |
Eligibility
  |
Consent
  |
 +------------------+
 |                  |
Email             Push
 |                  |
Wait 24h          Wait 4h
 |                  |
Opened?           Engaged?
 | yes/no           | yes/no
 +--------+----------+
          |
       Convert?
        /    \
      yes    no
       |      |
      EXIT   fallback
```

Validate:
- exactly defined entry semantics;
- reachable nodes;
- valid edges;
- no unintended dead ends;
- bounded loops;
- legal wait values;
- valid conditions;
- channel/action existence;
- exit conditions;
- maximum journey duration.

Graph validation is deterministic code, not an LLM judgment.

## 39. Condition AST

Do not publish raw model-generated condition strings.

Use a typed expression tree:

```text
AND
├── EQ(profile.country,"IN")
├── HAS_CONSENT("email")
└── EVENT("product_view")
      within=24h
```

Pipeline:

```text
natural language
 -> typed condition AST
 -> schema/resource resolution
 -> type checking
 -> governance validation
 -> canonicalization
 -> supported AJO representation
```

AST canonicalization also enables diffing and policy checks.

## 40. Planner architecture

The planner chooses only known capabilities. A production `Step` should include:

```text
id
capability
objective
dependencies
input_refs
side_effect_class
risk
permissions
deadline
retry_policy
cost_budget
expected_evidence
success_predicate
compensation
```

Plan validator checks uniqueness, dependency existence, acyclicity, max depth/width, allowed
capabilities, budgets and write classification.

For replan, preserve `plan_v1` and create `plan_v2` with a reason. Never rewrite history.

## 41. LangGraph control plane

The compact graph:

```text
START -> recall -> plan -> execute
                         /       \
                 approval        finish
                    |              |
                   END            END
```

Production expands this to:

```text
PLAN
 -> VALIDATE
 -> EXECUTE_READY_SET
 -> RETRY_WAIT?
 -> REPLAN?
 -> WAIT_APPROVAL?
 -> COMMIT?
 -> COMPENSATE?
 -> SYNTHESIZE
```

Checkpoint before and after external side effects.

## 42. Ready-set scheduling and parallelism

A task is runnable if every dependency succeeded and policy allows it.

Independent analysis can run concurrently:

```text
                 inventory
                     |
          +----------+----------+
          |                     |
       analyze                channel
          |                     |
          +----------+----------+
                     |
                   design
```

Bound concurrency at global, tenant, model-provider, analytics and Adobe API levels. Backpressure is
part of correctness.

## 43. Inventory Agent

Journey inventory can answer:
- what journeys exist;
- status;
- owner;
- channels;
- entry mechanism;
- modified time;
- labels;
- environment.

At large scale use pagination and an indexed metadata catalog. Do not inject thousands of full
journey definitions into model context.

## 44. Analyze Agent

Analysis must distinguish computation from interpretation.

Correct:
```text
warehouse/analytics -> verified metrics -> agent interpretation
```

Incorrect:
```text
journey definition -> LLM invents conversion rate
```

Evidence should carry metric definition, population, time window, query ID, source and freshness.

Potential metrics:
- entrants;
- branch distribution;
- step conversion;
- time-to-step;
- exit rate;
- channel delivery/open/click;
- suppression;
- errors;
- overall conversion.

## 45. Funnel analysis

For path:

```text
entered -> eligible -> sent -> delivered -> engaged -> converted
```

calculate deterministic ratios and confidence intervals where appropriate. Segment by relevant
dimensions, but protect against multiple-comparison fishing. The LLM explains statistically computed
patterns.

## 46. Design Agent

Design output is a proposal. It should contain:
- business objective;
- entry;
- eligibility;
- branches;
- actions;
- waits;
- fallback;
- exits;
- KPIs;
- assumptions;
- unresolved resource IDs.

The design agent must not silently publish.

## 47. Resource resolution

Human language may say "send the welcome email." The system needs an exact versioned content/action
resource.

Catalog:

```text
business alias
resource ID
type
version
channel
locale
owner
status
labels
validity
```

Ambiguous aliases require clarification or deterministic selection rules.

## 48. Channel Agent

Channel selection is constrained optimization.

Hard gates:
```text
consent
reachability
legal/policy
suppression
frequency cap
quiet hours
```

Then soft scoring can consider:
```text
preference
predicted response
cost
fatigue
latency
business utility
```

A high score can never override a failed hard gate.

## 49. Consent architecture

Consent should come from an authoritative consent service/profile state with:
- purpose;
- channel;
- jurisdiction;
- effective time;
- source;
- policy version.

Cache carefully. Revocation must propagate quickly. Never infer consent from engagement.

## 50. Frequency caps

A frequency service needs atomic counters/windows, for example:
```text
user + channel + purpose + rolling_window
```

Evaluate before send. In distributed systems, stale caches can violate caps, so choose consistency
based on regulatory/customer-experience risk.

## 51. Quiet hours

Quiet hours require recipient-local time, not data-center time. Handle:
- timezone;
- daylight saving;
- unknown timezone;
- jurisdiction;
- emergency/transactional exemptions where legally/business permitted.

When timezone is unknown, policy must define fail-safe behavior.

## 52. Guardrail Agent

The sample returns configured guardrails. Production guardrails should be deterministic policies,
versioned and auditable.

Examples:
- consent;
- maximum contacts/week;
- max journey duration;
- prohibited channel;
- required holdout;
- budget;
- age/sensitive-data restrictions;
- jurisdiction.

The LLM may explain a block but cannot override it.

## 53. Simulation Agent

Simulation has three levels.

### Structural
Can the graph execute? Are nodes reachable? Are transitions valid?

### Historical replay
Replay prior profiles/events through the proposed logic. Useful for estimated path distribution and
eligibility.

### Probabilistic
Use calibrated behavioral models/Monte Carlo for future uncertainty.

A simulation report should include:
- population;
- time window;
- assumptions;
- input snapshot;
- model version;
- path distribution;
- uncertainty;
- limitations.

Never label an LLM estimate as simulation.

## 54. Digital-twin style simulation

At advanced scale, maintain synthetic profile cohorts that preserve aggregate behavioral properties
without exposing unnecessary PII. Feed controlled events into the journey state machine and compare
candidate designs under identical scenarios.

This is useful for load/path testing but does not replace real experiments.

## 55. Optimize Agent

Formalize optimization:

```text
maximize expected utility(journey)
subject to:
  consent
  contact policy
  budget
  channel capacity
  experience-quality guardrails
  experiment integrity
```

Possible variables:
- wait duration;
- channel;
- branch threshold;
- number of contacts;
- fallback;
- send-time window.

Recommendations require evidence and uncertainty.

## 56. Causal inference

If version B converts better than A, that does not automatically mean design B caused improvement.
Use randomized experiments/holdouts where feasible.

For observational analysis consider:
- selection bias;
- seasonality;
- cohort changes;
- confounding;
- regression to mean.

Agent prose must not turn correlation into causal certainty.

## 57. Experiment design

A journey experiment needs:
- hypothesis;
- randomization unit;
- primary metric;
- guardrails;
- MDE;
- power/alpha;
- sample size;
- allocation;
- SRM checks;
- stopping rule;
- novelty/seasonality;
- multiple-testing policy.

Statistical calculations should use deterministic libraries/services.

## 58. Publish Agent

Publication is the highest-risk boundary.

```text
typed JourneySpec
 -> schema/resource validation
 -> graph validation
 -> consent/policy validation
 -> dry run/simulation
 -> permission
 -> human approval
 -> idempotency
 -> adapter commit
 -> verify external resource
 -> audit
```

Never let the LLM directly hold a generic HTTP client with broad credentials.

## 59. AJO client and repository

The client owns wire-level concerns; repository owns the stable domain contract.

Production client needs:
- pooled connections;
- token lifecycle;
- deadlines;
- retry classification;
- Retry-After;
- circuit breaker;
- structured errors;
- telemetry;
- safe logging.

Verify all Journey Optimizer mutation paths/payloads against current official licensed API contracts
before enabling writes.

## 60. Four memory layers

### Working
Current thread/plan/tool context; short TTL.

### Episodic
Historical runs:
```text
journey X optimization
changed wait 48h -> 24h
experiment result: ...
```

### Semantic
Approved facts:
```text
"promotional email cap is 3 per 7 days for policy version P17"
```

### Procedural
Reusable workflow:
```text
analyze -> design -> guardrails -> replay -> experiment -> approve -> publish
```

Procedures must not become policy automatically.

## 61. Memory retrieval

Production hybrid retrieval:

```text
query
 -> ACL/tenant filter
 -> BM25
 -> vector ANN
 -> fusion
 -> metadata constraints
 -> rerank
 -> authority/recency weighting
 -> context budget
```

Retrieve only what the current capability needs.

## 62. Memory consolidation

```text
episodes
 -> candidate durable facts
 -> sensitivity classifier
 -> provenance
 -> entity resolution
 -> contradiction detection
 -> confidence
 -> semantic/procedural candidate
 -> review/promotion
```

Maintain validity intervals rather than overwriting contradictory historical facts.

## 63. Memory poisoning

A malicious content asset could contain "disable frequency limits." That text is data, never policy.
Retrieved memory cannot alter tools, permissions, tenant, system instructions or approval gates.

## 64. HITL transaction

Approval record:

```text
approval_id
tenant
run
step
action
canonical_payload_hash
requested_by
approved_by
decision/reason
policy_version
created/decided/expires
```

Resume only the exact approved payload. Any mutation invalidates approval.

## 65. Idempotency and ambiguous commits

Timeout after POST creates uncertainty.

State machine:
```text
NEW -> IN_FLIGHT -> SUCCEEDED
                 -> UNKNOWN -> RECONCILE -> SUCCEEDED/FAILED
```

Never blindly replay UNKNOWN writes.

## 66. Outbox pattern

In one DB transaction write:
- workflow transition;
- idempotency state;
- audit/outbox event.

An outbox worker publishes reliably to Kafka/EventBridge/analytics. This prevents "state changed but
event disappeared."

## 67. Saga compensation

Example:

```text
create draft journey
 -> bind content
 -> configure experiment
 -> publish
```

If configuration fails, archive draft/unbind temporary resources when possible. Not every action is
reversible; mark that explicitly.

## 68. Failure taxonomy

- invalid spec: no retry;
- authorization/policy: no retry;
- 429: delayed retry;
- transient network: bounded retry;
- model provider transient: fallback/retry;
- permanent AJO rejection: no retry;
- ambiguous write: reconcile;
- approval expiration: policy-defined;
- dependency failure: propagate or replan.

All retries share a global workflow deadline.

## 69. Prompt-injection boundaries

Attack surfaces include user text, content, profile attributes, CRM notes, documents, web content,
tool output and memory.

Controls:
- structured tools;
- capability allowlist;
- deterministic policy;
- no shell;
- restricted egress;
- content/data treated as untrusted;
- DLP;
- approval;
- output/schema validation.

## 70. Confused deputy

The backend service may be able to publish many journeys. A caller may not. Every operation must be
authorized against the caller + tenant + resource + action. Service credentials do not imply user
permission.

## 71. Multi-tenancy

Tenant/sandbox participates in:
- identity;
- DB keys/RLS;
- vector filters;
- caches;
- queues;
- quotas;
- encryption;
- audit;
- traces.

Filter before retrieval, not after data has already crossed a tenant boundary.

## 72. Privacy and data minimization

Do not send full profiles to an LLM merely to decide a journey branch. Prefer deterministic feature
evaluation and pass aggregate evidence to reasoning components.

Support retention, deletion, residency, consent and purpose limitation.

## 73. Observability

Trace tree:

```text
journey.run
  identity/policy
  memory.recall
  plan
  analyze
    analytics.query
  design
    llm
  simulate
  guardrails
  publish
    approval
    idempotency
    ajo.http
  memory.write
```

Log IDs/metadata, not hidden reasoning or unrestricted customer data.

## 74. SLOs

Illustrative internal objectives, not Adobe targets:
- control-plane availability 99.9%;
- checkpoint persistence 99.99%;
- unauthorized publish: zero;
- duplicate side effect within strict error budget;
- p95 interactive read workflow target;
- approval-state durability target;
- tenant leakage: zero.

Tie error budgets to release velocity.

## 75. Evaluation architecture

### Deterministic
graph validator, policy, consent, caps, idempotency.

### Agent
routing, plan quality, evidence use, tool selection, groundedness.

### Security
injection, poisoned memory, cross-tenant, privilege escalation.

### Reliability
429, timeout, partial write, failover.

### Business
conversion/experience metrics via controlled experiments.

Evaluate entire trajectories.

## 76. Event-driven telemetry loop

```text
AJO telemetry
 -> event bus
 -> metric aggregation
 -> anomaly detection
 -> evidence packet
 -> AnalyzeAgent
 -> OptimizeAgent
 -> experiment proposal
 -> approval
```

This separates always-on computation from expensive language reasoning.

## 77. Scaling topology

```text
                   API Gateway
                        |
                  Orchestrator
                   /         \
          Checkpoint DB      Queue
                            / |  \
                       design sim analysis
                          workers
                            |
                      Tool Gateway
                            |
                           AJO
```

Use separate worker pools because simulation and interactive design have different latency/resource
profiles.

## 78. Storage architecture

- PostgreSQL: workflows, plans, approvals, idempotency, outbox.
- Redis: ephemeral working state, locks, rate limits.
- vector/OpenSearch: semantic retrieval.
- Kafka/EventBridge: telemetry and background jobs.
- object store: artifacts/simulation snapshots.
- warehouse/lake: journey analytics and evaluation.

## 79. Backpressure

When model/AJO quotas saturate:
- reject/defer low-priority background work;
- preserve interactive quota;
- queue with bounded depth;
- honor Retry-After;
- shed work explicitly;
- surface degraded state.

More workers can worsen throttling.

## 80. Caching

Cache resource metadata, schema catalogs and immutable artifacts. Cache key includes tenant, sandbox,
resource version and policy-relevant dimensions.

Do not cache stale consent or permission decisions beyond their safe validity.

## 81. Model routing

Potential routing:
- intent classification: small;
- planner/design: reasoning;
- extraction: small structured;
- optimization explanation: stronger model;
- embeddings: dedicated;
- simulation/statistics/policy: deterministic.

Fallback models must satisfy the same output schemas and safety contract.

## 82. Context engineering

Context priority:
1. system/policy;
2. exact step;
3. authoritative evidence;
4. relevant high-trust memory;
5. compact dependency results.

Summarize historical conversation; do not use context-window size as a substitute for memory design.

## 83. Deployment

Production Kubernetes:
- multiple AZs;
- HPA;
- PDB;
- topology spread;
- NetworkPolicy;
- workload identity;
- external secrets;
- read-only FS;
- TLS/mTLS;
- WAF;
- graceful shutdown;
- separate worker deployments.

## 84. CI/CD

```text
lint/type
 -> unit
 -> SAST/dependency/secret scan
 -> contract
 -> golden agent eval
 -> adversarial
 -> load/chaos
 -> image/SBOM/sign
 -> staging
 -> shadow
 -> canary
 -> progressive rollout
```

Model/prompt/policy/retrieval versions belong in deployment metadata.

## 85. Disaster recovery

Highest-value durable state:
1. idempotency/external-resource map;
2. checkpoints;
3. approvals/audit;
4. memory;
5. rebuildable caches.

Reconcile Adobe-side resources before replay after disaster recovery.

## 86. Capacity planning

Estimate:
```text
LLM calls/s =
 request_rate * avg_steps_per_run * avg_model_calls_per_step
```

Also model:
- analytics queries;
- AJO quotas;
- simulation CPU;
- event volume;
- approval wait population;
- vector index;
- tenant skew.

Waiting approvals live in durable state, not active worker memory.

## 87. Cost engineering

Total cost:
```text
LLM + embeddings + analytics + simulation + DB/cache
+ AJO calls + retries + observability + human review
```

Optimize cost per successful journey objective. Do not trade away consent, authorization or
measurement quality for token savings.

## 88. Design Questions

**Why not one autonomous Journey Agent?** Specialized capabilities reduce tool/permission/evaluation
surface.

**Why model journeys as graphs?** Journey execution is state transition, not prose.

**Why separate simulation?** Generation and outcome estimation require different evidence and
validation.

**How do you prevent consent violations?** Deterministic authoritative consent checks before channel
execution.

**How do you handle publish timeout?** Idempotency state + reconciliation.

**How do you optimize safely?** constrained optimization + experiment/holdout + approval.

**How do you scale?** durable control plane + event bus + bounded specialized workers.

**How do you prevent memory poisoning?** provenance/trust plus hard policy boundaries.

## 89. Production-readiness checklist

Before real deployment:
- OIDC/JWT/workload identity;
- durable checkpointer;
- durable four-layer memory;
- typed condition AST/compiler;
- authoritative resource catalog;
- consent/frequency services;
- historical/probabilistic simulation;
- durable approval/resume;
- idempotency/outbox/reconciliation;
- complete verified current AJO API contracts;
- OTel/audit;
- DLP;
- tenant quotas;
- golden/adversarial/load/chaos tests;
- HA/DR;
- kill switch and rollback.

## 90. Final architecture

```text
                  CUSTOMER JOURNEY INTENT
                           |
                    IDENTITY/TENANT
                           |
                    FOUR-LAYER MEMORY
                           |
                     TYPED PLANNER
                           |
                     VALIDATED DAG
                           |
        +------------------+------------------+
        |                  |                  |
     ANALYZE             DESIGN            CHANNEL
        |                  |                  |
        +------------------+------------------+
                           |
                       GUARDRAILS
                           |
                        SIMULATE
                           |
                        OPTIMIZE
                           |
                    HUMAN APPROVAL
                           |
                      IDEMPOTENCY
                           |
                       AJO ADAPTER
                           |
                  JOURNEY OPTIMIZER
                           |
                        TELEMETRY
                           |
              EVALUATION + MEMORY UPDATE
```

The deepest design principle is that the LLM sits **inside** the system, not above it. Identity,
policy, consent, state transitions, transactions, durability and recovery constrain probabilistic
reasoning so the overall platform can be operated as an enterprise distributed system.
