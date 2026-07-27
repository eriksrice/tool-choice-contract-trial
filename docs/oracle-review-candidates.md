# Milestone 2B Oracle Review Candidates

## Status and purpose

Milestone 2B is a `PROVISIONAL_REVIEW_CANDIDATE`. The repository owner has reviewed all 12 cases without policy outputs, accepting 11 proposals and disputing one. The disagreement remains unadjudicated, independent review has not been performed, and the bundle is not frozen. This milestone demonstrates versioned clause expansion and an inspectable oracle-authoring workflow; it does not claim independently reviewed oracle truth, a frozen benchmark, or policy performance.

The v2 artifact layer is isolated from the frozen Milestone 1 and Milestone 2A v1 artifacts. `PolicyViewV2` contains only an opaque scenario ID, a `TaskContractV2`, and available `ToolManifestV2` records. Family labels, variant labels, proposed answers, rationales, reviews, and adjudication fields remain evaluator-only.

## Contract clauses

V2 retains capability, authority, and citation compatibility while adding only three authorized clause classes:

- input requirements: each required input profile must appear in a tool's accepted profiles;
- output/evidence requirements: each required output profile must appear in a tool's produced profiles, and required citations need declared citation capability;
- explicit prohibition: a forbidden tool is inadmissible even if every other clause matches.

The explicit registry binds the six relation clauses to canonical contract and manifest fields. Its hash is recorded in every validation finding and the provisional manifest. Under the current checker semantics, an unavailable forbidden tool ID is schema-valid but semantically invalid, so the relation checker returns `CONTRACT_INVALID` rather than treating the fixture relationship as defective. The owner review disputes that rule for `v2_scenario_012`, judging the unavailable prohibition redundant and both available tools admissible. Neither the checker nor the proposed expectation was changed, and the conflict remains visible for later adjudication.

## Review-candidate families

The bundle contains three neutral fictional enterprise knowledge-work families, each with four cases:

| Family | Controlled cases |
| --- | --- |
| Input profiles | Unique `structured_json`; unique `tabular_csv`; unsupported input with no admissible tool; shared `plain_text` with multiple admissible tools. |
| Output/evidence profiles | Unique `structured_extracts`; unique `audit_table`; unsupported output with no admissible tool; shared `narrative_summary` with multiple admissible tools. Citation capability differs, but citations are not required in these four contracts, so the controlled output pairs remain single-clause. |
| Explicit prohibition | Forbid either otherwise admissible tool to flip the unique member; forbid both for no admissible tool; forbid an unavailable ID for intentional `CONTRACT_INVALID`. |

The input, output, and prohibition pairs are controlled as authoring structures. The frozen v1 counterfactual analyzer supports only the authority family, so no v2 counterfactual findings or matched-pair policy-sensitivity results are claimed.

## Independence and review workflow

The command processes artifacts in this order:

1. load and validate v2 policy-visible scenarios;
2. compute every admissibility relation without expectations, reviews, or policy decisions;
3. load and link separately stored proposed expectations and review records;
4. compare computed and proposed state, admissible set, and contract-faithful response;
5. classify review readiness and evaluation-unit status;
6. source-verify persisted findings and the provisional manifest against all input artifacts;
7. write canonical findings, a pure Markdown review packet, a provisional manifest, and an invalid-unit register.

Codex-authored expectations remain explicitly `PROPOSED`. The checked-in completed records identify only the role `owner_reviewer`; they do not invent or encode a person's identity. Each records that the review was performed without policy outputs. The dispositions are:

- 11 `AGREE` records whose reviewed states and sets cohere with both the proposals and computed relations;
- one `DISAGREE` record for `v2_scenario_012`, with reviewed state `MULTIPLE_ADMISSIBLE` and admissible set `{v2_tool_005, v2_tool_006}`;
- zero `PENDING` or `ADJUDICATED` records.

The owner review does not count as independent review. The eleven coherent agreements are row-level ready for scoring and freeze under the lifecycle mechanics, but the bundle remains provisional and unfrozen. The unadjudicated disagreement is `ADJUDICATION_REQUIRED`, `EVALUATION_UNIT_INVALID`, and not ready for scoring or freeze.

The owner also accepted `v2_scenario_007` while noting a nonblocking ecological-validity concern: `verified_transcript` is somewhat artificial for the stated knowledge-packet task and should be reconsidered before any claim-grade freeze.

## Invalidity boundary

`CONTRACT_INVALID` is one of the four relation states. It follows from a deliberate policy-visible semantic defect and can become scoreable after coherent review.

`EVALUATION_UNIT_INVALID` is not a relation state. It identifies a defective proposal, review, adjudication, or linkage, such as a completed disagreement without adjudication or an agreement whose values contradict the proposal or computed relation. Such units remain visible and cannot enter policy metrics. Duplicate or unknown linked rows are rejected as artifact-integrity failures before a bundle is produced.

The current invalid-unit register contains exactly `v2_scenario_012`. Its computed relation remains `CONTRACT_INVALID`, while its owner-reviewed judgment remains `MULTIPLE_ADMISSIBLE`; the lifecycle preserves both positions without adjudicating them.

## Provisional manifest

The typed manifest records schema versions, per-scenario artifact hashes, scenario/expectation/review bundle hashes, the relation-registry hash, computed state counts, pending-review count, invalid-unit count, contract-invalid count, and the fixed bundle status `PROVISIONAL_REVIEW_CANDIDATE`.

Because its values cover the scenario, expectation, review, and finding artifacts, any mutation changes the manifest content and its canonical hash. The manifest records reproducibility and review state; it does not certify the substantive correctness of a proposal.

Schema validation alone does not make a loaded finding or manifest trusted. Before rendering the review packet, the workflow independently recomputes relations, artifact hashes, lifecycle fields, witnesses, counts, and manifest rows from the source scenarios, expectations, and reviews. Any difference is an artifact-integrity failure.

## Human review gate

Before any v2 freeze decision, independent review must inspect each scenario without policy outputs, and the `v2_scenario_012` disagreement must be adjudicated. The owner review recorded here is not a substitute for either gate. Policy comparison, v2 counterfactual validation, broader scenario coverage, live-model evaluation, benchmark scaling, and Milestone 3 require separate authorization.

Run and byte-compare the candidate using [Reproducibility](reproducibility.md). The wider interpretation boundary is documented in [Limitations](limitations.md).
