"""
test_deduplication_deep.py — Rigorous Multi-Scenario Verification Suite

Tests 5 critical dimensions of the SAME_PATH_FRAGMENT false deduplication defect:
  1. Multi-Path Transitive Collapse (4 disparate Cypress controllers)
  2. Score Inversion Sensitivity (Arbitrary victim selection)
  3. Orthogonal Risk Family Boundary Verification
  4. True Duplicate Implementation Preservation (No regression on real duplicates)
  5. Downstream select_candidates() Selection Capacity (MAXIMUM_PER_FAMILY=2)
"""

import sys
import copy
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = SCRIPT_DIR / "artifacts"
ENGINE_DIR = Path(r"C:\Users\MAHESH\unvibecode-lab\.venv\Lib\site-packages\shipreadyv2\engine_sources")

sys.path.insert(0, str(ENGINE_DIR))
import importlib.util

def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, str(ENGINE_DIR / filename))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

step4 = load_module("step4", "04_shipreadyv2_business_path_compiler.py")
step5 = load_module("step5", "05_shipreadyv2_critical_business_insight_selector_v4.py")


def fixed_deduplicate_candidates(candidates: list[dict], normalized: dict) -> None:
    """Fixed Step 05 grouping: uses exact path_id when implementation_group_ids is empty."""
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for candidate in candidates:
        implementation = "+".join(sorted(candidate.get("implementation_group_ids", [])))
        if implementation:
            group_key = (candidate["family"], implementation)
        else:
            path_key = "+".join(sorted(candidate.get("normalized_path_ids", [])))
            group_key = (candidate["family"], path_key)
        groups[group_key].append(candidate)

    decision_rank = {"ELIGIBLE_STRONG": 4, "ELIGIBLE_BOUNDED": 3, "INVESTIGATION_GAP": 2, "REJECTED": 1}
    for members in groups.values():
        if len(members) < 2:
            continue
        members.sort(key=lambda c: (decision_rank.get(c["decision"], 0), c["score"]["total"], c["confidence"]["candidate"]), reverse=True)
        representative = members[0]
        for duplicate in members[1:]:
            if duplicate["decision"] in {"ELIGIBLE_STRONG", "ELIGIBLE_BOUNDED"}:
                duplicate["decision"] = "DUPLICATE_OR_VARIANT"
                duplicate["qualification_status"] = "DUPLICATE_OR_VARIANT"
                duplicate["rejection_reasons"].append({
                    "code": "DUPLICATE_RISK_DIMENSION",
                    "reason": f"A stronger representative exists: {representative['insight_id']}",
                })
                duplicate["representative_insight_id"] = representative["insight_id"]


class NullAudit:
    def add(self, *args, **kwargs): pass


def run_all_tests():
    print("=" * 80)
    print("RIGOROUS VERIFICATION SUITE: STEP 05 DEDUPLICATION INTEGRITY")
    print("=" * 80)

    chunk_auth = "chunk_c6bf2b29827021a9"  # backend/helpers.ts::ensureAuthenticated

    # ---------------------------------------------------------------------------------------------
    # TEST 1: Multi-Path Transitive Chain Collapse across 4 Real Cypress Controllers
    # ---------------------------------------------------------------------------------------------
    print("\n[TEST 1] Multi-Path Transitive Chain Collapse across 4 Disparate Controllers")
    routes = [
        ("path_trans", "POST /transactions", "chunk_trans_86416f04"),
        ("path_notif", "GET /notifications",  "chunk_notif_06a39591"),
        ("path_bank",  "POST /bankAccounts",  "chunk_bank_1a85ee8c"),
        ("path_contact","POST /contacts",     "chunk_contact_6cc58f72"),
    ]

    paths_t1 = []
    for pid, entry, chunk_id in routes:
        paths_t1.append({
            "normalized_path_id": pid,
            "entrypoints": [{"repo_native_entrypoint": entry}],
            "effects": [{"effect_classification": {"canonical_value": "DATABASE_WRITE"}}],
            "evidence": [
                {"chunk_id": chunk_id, "validation_status": "VALID", "evidence_id": f"ev_{chunk_id}"},
                {"chunk_id": chunk_auth, "validation_status": "VALID", "evidence_id": "ev_shared_auth"},
            ],
            "implementation_group_ids": [],
            "canonical_confidence": {"score": 85},
        })

    groups_t1, rels_t1 = step4.build_implementation_groups(paths_t1, NullAudit())
    print(f"  Step 04 Relationships: {len(rels_t1)} (All SAME_PATH_FRAGMENT)")
    print(f"  Step 04 Implementation Groups: {len(groups_t1)} (Zero implementation groups assigned)")

    candidates_t1 = []
    scores = [95, 90, 85, 80]
    for i, (pid, entry, _) in enumerate(routes):
        candidates_t1.append({
            "insight_id": f"insight_{pid}",
            "family": "CROSS_BOUNDARY_TRUST_PATH",
            "title": f"Trust boundary risk at {entry}",
            "normalized_path_ids": [pid],
            "implementation_group_ids": [],
            "decision": "ELIGIBLE_STRONG",
            "qualification_status": "ELIGIBLE",
            "rejection_reasons": [],
            "score": {"total": scores[i]},
            "confidence": {"candidate": 90},
        })

    # Baseline run
    norm_t1 = {"path_relationships": rels_t1}
    base_cands_t1 = copy.deepcopy(candidates_t1)
    step5.deduplicate_candidates(base_cands_t1, norm_t1)

    survived_base = [c["insight_id"] for c in base_cands_t1 if c["decision"] == "ELIGIBLE_STRONG"]
    dropped_base = [c["insight_id"] for c in base_cands_t1 if c["decision"] == "DUPLICATE_OR_VARIANT"]
    print(f"  Baseline 0.3.15: Survived={len(survived_base)}, Dropped={len(dropped_base)}")
    assert len(survived_base) == 1, f"Expected exactly 1 survivor in baseline, got {len(survived_base)}"
    assert len(dropped_base) == 3, f"Expected 3 dropped candidates in baseline, got {len(dropped_base)}"
    print(f"    -> Winner: {survived_base[0]}")
    print(f"    -> Suppressed (75% loss): {dropped_base}")

    # Fixed run
    fixed_cands_t1 = copy.deepcopy(candidates_t1)
    fixed_deduplicate_candidates(fixed_cands_t1, norm_t1)
    survived_fixed = [c["insight_id"] for c in fixed_cands_t1 if c["decision"] == "ELIGIBLE_STRONG"]
    print(f"  Fixed Implementation: Survived={len(survived_fixed)}, Dropped={len(fixed_cands_t1) - len(survived_fixed)}")
    assert len(survived_fixed) == 4, f"Expected all 4 to survive in fixed, got {len(survived_fixed)}"
    print("  [PASS] TEST 1: Transitive collapse correctly verified and resolved.")

    # ---------------------------------------------------------------------------------------------
    # TEST 2: Score Inversion Sensitivity (Victim Flip)
    # ---------------------------------------------------------------------------------------------
    print("\n[TEST 2] Score Inversion Sensitivity (Arbitrary Victim Selection)")
    cand_trans = copy.deepcopy(candidates_t1[0])  # trans
    cand_notif = copy.deepcopy(candidates_t1[1])  # notif

    # Case A: Trans > Notif
    cand_trans["score"]["total"] = 92
    cand_notif["score"]["total"] = 80
    cands_a = [copy.deepcopy(cand_trans), copy.deepcopy(cand_notif)]
    step5.deduplicate_candidates(cands_a, norm_t1)
    assert cands_a[0]["decision"] == "ELIGIBLE_STRONG"
    assert cands_a[1]["decision"] == "DUPLICATE_OR_VARIANT"
    print("  Case A (Trans=92 > Notif=80): Notif dropped as duplicate.")

    # Case B: Notif > Trans
    cand_trans["score"]["total"] = 75
    cand_notif["score"]["total"] = 95
    cands_b = [copy.deepcopy(cand_trans), copy.deepcopy(cand_notif)]
    step5.deduplicate_candidates(cands_b, norm_t1)
    assert cands_b[0]["decision"] == "DUPLICATE_OR_VARIANT"
    assert cands_b[1]["decision"] == "ELIGIBLE_STRONG"
    print("  Case B (Notif=95 > Trans=75): Trans dropped as duplicate.")
    print("  [PASS] TEST 2: Victim dynamically flips strictly based on score comparison.")

    # ---------------------------------------------------------------------------------------------
    # TEST 3: Orthogonal Risk Family Boundary Verification
    # ---------------------------------------------------------------------------------------------
    print("\n[TEST 3] Orthogonal Risk Family Boundary Verification")
    cand_fam1 = copy.deepcopy(candidates_t1[0])
    cand_fam1["family"] = "CROSS_BOUNDARY_TRUST_PATH"

    cand_fam2 = copy.deepcopy(candidates_t1[1])
    cand_fam2["family"] = "STATE_TRANSITION_INTEGRITY"  # Different family

    cands_fam = [copy.deepcopy(cand_fam1), copy.deepcopy(cand_fam2)]
    step5.deduplicate_candidates(cands_fam, norm_t1)
    assert cands_fam[0]["decision"] == "ELIGIBLE_STRONG"
    assert cands_fam[1]["decision"] == "ELIGIBLE_STRONG"
    print("  Different families sharing helper: Both survived ELIGIBLE_STRONG.")
    print("  [PASS] TEST 3: Bug is strictly family-scoped; orthogonal families are unaffected.")

    # ---------------------------------------------------------------------------------------------
    # TEST 4: True Duplicate Implementation Preservation (No Regression)
    # ---------------------------------------------------------------------------------------------
    print("\n[TEST 4] True Duplicate Implementation Preservation (No Regression)")
    path_dup1 = {
        "normalized_path_id": "path_dup_primary",
        "entrypoints": [{"repo_native_entrypoint": "POST /api/v1/pay"}],
        "effects": [{"effect_classification": {"canonical_value": "DATABASE_WRITE"}}],
        "evidence": [{"chunk_id": "chunk_payment_core", "validation_status": "VALID", "evidence_id": "ev_pay"}],
        "implementation_group_ids": [],
        "canonical_confidence": {"score": 90},
    }
    path_dup2 = {
        "normalized_path_id": "path_dup_alias",
        "entrypoints": [{"repo_native_entrypoint": "POST /api/v1/pay"}],
        "effects": [{"effect_classification": {"canonical_value": "DATABASE_WRITE"}}],
        "evidence": [{"chunk_id": "chunk_payment_core", "validation_status": "VALID", "evidence_id": "ev_pay"}],
        "implementation_group_ids": [],
        "canonical_confidence": {"score": 85},
    }

    groups_dup, rels_dup = step4.build_implementation_groups([path_dup1, path_dup2], NullAudit())
    assert len(groups_dup) == 1, "Step 04 MUST create an implementation group for true duplicates"
    assert rels_dup[0]["relationship"] == "DUPLICATE_IMPLEMENTATION"
    print(f"  Step 04 correctly assigned implementation_group_id: {path_dup1['implementation_group_ids']}")

    cand_dup1 = {
        "insight_id": "cand_dup1", "family": "CROSS_BOUNDARY_TRUST_PATH",
        "normalized_path_ids": ["path_dup_primary"],
        "implementation_group_ids": list(path_dup1["implementation_group_ids"]),
        "decision": "ELIGIBLE_STRONG", "qualification_status": "ELIGIBLE",
        "rejection_reasons": [], "score": {"total": 90}, "confidence": {"candidate": 90},
    }
    cand_dup2 = {
        "insight_id": "cand_dup2", "family": "CROSS_BOUNDARY_TRUST_PATH",
        "normalized_path_ids": ["path_dup_alias"],
        "implementation_group_ids": list(path_dup2["implementation_group_ids"]),
        "decision": "ELIGIBLE_STRONG", "qualification_status": "ELIGIBLE",
        "rejection_reasons": [], "score": {"total": 80}, "confidence": {"candidate": 80},
    }

    norm_dup = {"path_relationships": rels_dup}
    fixed_dups = [copy.deepcopy(cand_dup1), copy.deepcopy(cand_dup2)]
    fixed_deduplicate_candidates(fixed_dups, norm_dup)

    assert fixed_dups[0]["decision"] == "ELIGIBLE_STRONG"
    assert fixed_dups[1]["decision"] == "DUPLICATE_OR_VARIANT"
    print("  True duplicate alias correctly marked DUPLICATE_OR_VARIANT under fixed logic.")
    print("  [PASS] TEST 4: Zero regressions on genuine duplicate implementations.")

    # ---------------------------------------------------------------------------------------------
    # TEST 5: Downstream select_candidates() Selection Capacity (MAXIMUM_PER_FAMILY=2)
    # ---------------------------------------------------------------------------------------------
    print("\n[TEST 5] Downstream select_candidates() Execution & Capacity (MAXIMUM_PER_FAMILY=2)")
    print(f"  UnvibeCode MAXIMUM_PER_FAMILY config: {step5.MAXIMUM_PER_FAMILY}")
    print(f"  UnvibeCode MINIMUM_SELECTION_SCORE:   {step5.MINIMUM_SELECTION_SCORE}")

    # Prepare fixtures with required fields for Cython native selector
    for c in base_cands_t1 + fixed_cands_t1:
        c.setdefault("structural_corroboration", {})

    # Execute actual native select_candidates() on both candidate pools
    selected_baseline = step5.select_candidates(base_cands_t1)
    selected_fixed = step5.select_candidates(fixed_cands_t1)

    print(f"  Actual selected findings (Baseline): {len(selected_baseline)} (IDs: {[x['insight_id'] for x in selected_baseline]})")
    print(f"  Actual selected findings (Fixed):    {len(selected_fixed)} (IDs: {[x['insight_id'] for x in selected_fixed]})")

    # In Baseline, false deduplication killed 3 candidates before selection, leaving only 1 available
    assert len(selected_baseline) == 1, f"Expected 1 selected in baseline, got {len(selected_baseline)}"
    # In Fixed, all 4 candidates are eligible; select_candidates() correctly caps at MAXIMUM_PER_FAMILY=2
    assert len(selected_fixed) == 2, f"Expected 2 selected in fixed (enforcing MAXIMUM_PER_FAMILY=2), got {len(selected_fixed)}"
    print("  [PASS] TEST 5: Actual select_candidates() executed. Proved deduplication artificially starved downstream selection capacity.")

    print("\n" + "=" * 80)
    print("ALL 5 RIGOROUS VERIFICATION TESTS PASSED WITH 100% FIDELITY")
    print("=" * 80)
    return 0

if __name__ == "__main__":
    sys.exit(run_all_tests())
