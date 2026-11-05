# UnvibeCode 0.3.15: `SAME_PATH_FRAGMENT` Candidate Deduplication Mechanism Reproduction

This repository provides an autonomous, deterministic reproduction of a candidate deduplication defect in **UnvibeCode 0.3.15**.

---

## 1. Scope & Evidence Status

To maintain strict technical rigor, this reproduction distinguishes between established empirical facts and mechanism-level demonstrations:

| Evidence Component | Status | What It Establishes |
| :--- | :--- | :--- |
| **Authentic Cypress Chunks** | Verified | `backend/helpers.ts` (`chunk_c6bf2b29827021a9`) defines `ensureAuthenticated` (lines 98–113). |
| **Authentic Static Connections** | Verified | Verified cross-file imports show 8 routes (including `transaction-routes.ts` and `notification-routes.ts`) import `ensureAuthenticated`. |
| **Authentic Workflow IDs** | Verified | The completed Cypress analysis report (`business-workflows.html`) documents `business_path_e0050026511ee242` ("Create or update transactions") and `business_path_005a3eab6bf1afae` ("Create notifications and update notification fields") as distinct workflow areas sharing `ensureAuthenticated()`. |
| **Actual Step 04 Execution** | Verified | Given these paths, the installed `04_shipreadyv2_business_path_compiler.py` produces `SAME_PATH_FRAGMENT` (`SHARED_CODE_FRAGMENT`) and assigns **zero** implementation groups. |
| **Actual Step 05 Deduplication** | Verified | Given candidate fixtures for these paths in the same family, the installed `05_shipreadyv2_critical_business_insight_selector_v4.py` collapses them into the same grouping key and demotes one to `DUPLICATE_OR_VARIANT`. |
| **End-to-End Run Recovery** | Qualified | The completed Cypress run reported 10 rejected candidates and 0 findings. Because temporary candidate JSON files were cleaned up upon run completion, direct empirical attribution of those specific 10 rejections requires capturing uncleaned artifacts from a preserved run. |

---

## 2. Technical Defect Analysis

### Step 04: Shared Code is Not an Implementation Duplicate
In [`04_shipreadyv2_business_path_compiler.py:2998–3035`](file:///C:/Users/MAHESH/unvibecode-lab/.venv/Lib/site-packages/shipreadyv2/engine_sources/04_shipreadyv2_business_path_compiler.py#L2998), Step 04 detects that two paths share code chunks:
```python
elif left_chunks & right_chunks:
    relationship, rule_id, score = "SAME_PATH_FRAGMENT", "SHARED_CODE_FRAGMENT", 75

# Step 04 ONLY creates an implementation group for true duplicates/variants:
if relationship in {"DUPLICATE_IMPLEMENTATION", "IMPLEMENTATION_VARIANT"}:
    group_id = stable_id("implementation_group", relationship, left_id, right_id)
    left["implementation_group_ids"].append(group_id)
    right["implementation_group_ids"].append(group_id)
```
Step 04's canonical rationale explicitly states:
> *"Paths remain distinct; only their implementation relationship is grouped."*

### Step 05: Shared Fragments Used as Equivalence Partitions
In [`05_shipreadyv2_critical_business_insight_selector_v4.py:1443–1460`](file:///C:/Users/MAHESH/unvibecode-lab/.venv/Lib/site-packages/shipreadyv2/engine_sources/05_shipreadyv2_critical_business_insight_selector_v4.py#L1443), Step 05 inverts this contract:
```python
# 1. Filters specifically for SAME_PATH_FRAGMENT:
for relationship in normalized.get("path_relationships", []):
    if relationship.get("relationship") != "SAME_PATH_FRAGMENT":
        continue
    source = str(relationship.get("source_path_id"))
    target = str(relationship.get("target_path_id"))
    group = min(relationship_group.get(source, source), relationship_group.get(target, target))
    relationship_group[source] = group
    relationship_group[target] = group

# 2. When implementation_group_ids is empty, falls back to path_key:
for candidate in candidates:
    path_key = "+".join(sorted(relationship_group.get(path_id, path_id) for path_id in path_ids))
    implementation = "+".join(sorted(candidate.get("implementation_group_ids", [])))
    groups[(candidate["family"], implementation or path_key)].append(candidate)
```

> [!NOTE]
> **Algorithm Nuance**: The `min()` propagation in `relationship_group` assigns the lower path ID across immediate pairs but does not perform full Disjoint Set Union (union-find with path compression). Its grouping behavior is order-dependent across graph edges. However, for any directly connected pair of paths sharing a helper chunk, both paths receive the same minimum identifier. When neither candidate belongs to an implementation group, `groups[(candidate["family"], path_key)]` treats them as duplicates within their family.

---

## 3. Quick Start & Execution

### Prerequisites
- Python 3.10+
- `pip install unvibecode==0.3.15`

### 1. Run Single-Script Reproduction
```bash
python reproduce_bug.py
```
Executes actual Step 04 `build_implementation_groups()` and Step 05 `deduplicate_candidates()`, comparing Baseline 0.3.15 against a decoupled grouping fallback.

### 2. Run 5-Dimension Deep Verification Suite
```bash
python test_deduplication_deep.py
```
Verifies:
1. **Transitive Chain Collapse**: 4 distinct controllers sharing a helper experience a 75% finding suppression under baseline.
2. **Score Inversion Sensitivity**: Proves the demoted victim dynamically flips based on arbitrary total score ranking.
3. **Orthogonal Family Boundaries**: Confirms candidates from different risk families do not collide.
4. **True Duplicate Preservation**: Confirms genuine `DUPLICATE_IMPLEMENTATION` candidates remain deduplicated (zero regressions).
5. **Selection Capacity Integrity**: Executes actual native `select_candidates()` and verifies selection policy adherence (`MAXIMUM_PER_FAMILY=2`).

---

## 4. Proposed Architectural Fix

In [`05_shipreadyv2_critical_business_insight_selector_v4.py:1455–1460`](file:///C:/Users/MAHESH/unvibecode-lab/.venv/Lib/site-packages/shipreadyv2/engine_sources/05_shipreadyv2_critical_business_insight_selector_v4.py#L1455):

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

## 5. Summary Verdict

```text
RESULT: SAME_PATH_FRAGMENT deduplication behavior reproduced deterministically
using actual UnvibeCode 0.3.15 Step 04 and Step 05 functions with constructed candidate
fixtures and authentic Cypress repository-context evidence. End-to-end candidate
suppression in the completed Cypress analysis remains to be independently verified.
```
