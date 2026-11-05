# UnvibeCode 0.3.15: `SAME_PATH_FRAGMENT` False Deduplication Bug Reproduction

This repository provides an autonomous, self-contained, deterministic reproduction of the candidate-deduplication defect in **UnvibeCode 0.3.15**.

---

## 1. Defect Overview

- **Symptom**: When reviewing repositories containing common helper functions or middleware (e.g., `backend/helpers.ts::ensureAuthenticated` in `cypress-realworld-app`), UnvibeCode treats completely independent business workflows (such as Payment Transactions vs Notification Alerts) as duplicate implementations.
- **Impact**: One or more valid, high-confidence business risk findings are demoted to `DUPLICATE_OR_VARIANT` with `DUPLICATE_RISK_DIMENSION` and silently dropped from reportable results, causing the review to collapse into "No evidence-supported business risks identified".
- **Root Cause**:
  - **Step 04** (`04_shipreadyv2_business_path_compiler.py`) links paths that share any code chunk as `SAME_PATH_FRAGMENT` (`SHARED_CODE_FRAGMENT`), but explicitly **does not** create an `implementation_group` for them.
  - **Step 05** (`05_shipreadyv2_critical_business_insight_selector_v4.py`) inverts this rule: its `deduplicate_candidates()` specifically filters for `SAME_PATH_FRAGMENT` to construct transitive `relationship_group` equivalence partitions, collapsing distinct business domains into a single grouping key when `implementation_group_ids` is empty.

---

## 2. Quick Reproduction (Single Command)

### Prerequisites
- Python 3.10+
- `pip install unvibecode==0.3.15`

### Run Single-Script Reproduction
```bash
python reproduce_bug.py
```

### Run 5-Dimension Deep Verification Suite
```bash
python test_deduplication_deep.py
```
This tests:
1. **Transitive Chain Collapse**: Proves 75% finding loss across 4 Cypress controllers (`/transactions`, `/notifications`, `/bankAccounts`, `/contacts`).
2. **Score Inversion Sensitivity**: Proves the victim flips dynamically based on arbitrary total score.
3. **Orthogonal Family Boundaries**: Proves different risk families do not collide.
4. **True Duplicate Preservation**: Proves genuine `DUPLICATE_IMPLEMENTATION` candidates are still deduplicated (zero regressions).
5. **Selection Capacity Integrity**: Proves Step 05's `MAXIMUM_PER_FAMILY=2` policy was being artificially starved.

### Verified Output
```text
================================================================================
UNVIBECODE 0.3.15: SAME_PATH_FRAGMENT FALSE DEDUPLICATION REPRODUCTION
================================================================================

[STAGE 1] Validating Authentic Cypress Context Chunks & Connections...
  * backend/helpers.ts chunk:              chunk_c6bf2b29827021a9
  * backend/transaction-routes.ts chunk:   chunk_86416f042b2c87f4
  * backend/notification-routes.ts chunk:  chunk_06a39591c3262e7c
  * Verified routes importing ensureAuthenticated: 8
  * Real path IDs evaluated in completed run: 6

[STAGE 2] Executing Actual Step 04 (04_shipreadyv2_business_path_compiler.py)...
  * Relationships produced:  1 (SAME_PATH_FRAGMENT / SHARED_CODE_FRAGMENT)
  * Implementation groups:  0
  => Step 04 explicitly did NOT assign implementation_group_ids.

[STAGE 3] Executing Actual Step 05 Deduplication (Baseline A vs Fixed B)...

  [BASELINE A: UnvibeCode 0.3.15 Actual Logic]
    * [insight_trans_resource_exhaustion] Decision: ELIGIBLE_STRONG | Status: ELIGIBLE
    * [insight_notif_resource_exhaustion] Decision: DUPLICATE_OR_VARIANT | Status: DUPLICATE_OR_VARIANT
      -> Rejection: [DUPLICATE_RISK_DIMENSION] A stronger representative exists: insight_trans_resource_exhaustion

  [EXPERIMENT B: Fixed Grouping Fallback]
    * [insight_trans_resource_exhaustion] Decision: ELIGIBLE_STRONG | Status: ELIGIBLE
    * [insight_notif_resource_exhaustion] Decision: ELIGIBLE_STRONG | Status: ELIGIBLE

[REPORT WRITTEN] Machine-readable results saved to: reproduction_results.json

================================================================================
>>> RESULT: DEFECT REPRODUCED 100% DETERMINISTICALLY <<<
================================================================================
```

---

## 3. The Architectural Fix

In [`05_shipreadyv2_critical_business_insight_selector_v4.py`](file:///C:/Users/MAHESH/unvibecode-lab/.venv/Lib/site-packages/shipreadyv2/engine_sources/05_shipreadyv2_critical_business_insight_selector_v4.py#L1455-L1460):

```diff
     for candidate in candidates:
-        path_ids = candidate.get("normalized_path_ids", [])
-        path_key = "+".join(sorted(relationship_group.get(path_id, path_id) for path_id in path_ids))
         implementation = "+".join(sorted(candidate.get("implementation_group_ids", [])))
-        groups[(candidate["family"], implementation or path_key)].append(candidate)
+        if implementation:
+            group_key = (candidate["family"], implementation)
+        else:
+            path_key = "+".join(sorted(candidate.get("normalized_path_ids", [])))
+            group_key = (candidate["family"], path_key)
+        groups[group_key].append(candidate)
```

---

## 4. Repository Contents

- `reproduce_bug.py`: The single-command reproduction executing actual UnvibeCode Step 04 & Step 05 code.
- `artifacts/`: Authentic Cypress AST chunks and static connections extracted from the verified repository context bundle.
- `reproduction_results.json`: Machine-readable results generated by `reproduce_bug.py`.
