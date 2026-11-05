"""
reproduce_bug.py — Single-Script Reproduction of UnvibeCode 0.3.15 SAME_PATH_FRAGMENT Defect

Executes actual UnvibeCode Step 04 & Step 05 engine code against authentic
Cypress RealWorld App AST chunks, static connections, and workflow paths.

Usage:
    python reproduce_bug.py
"""

import sys
import json
import copy
import re
from pathlib import Path
from collections import defaultdict

# -------------------------------------------------------------------------------------------------
# 1. Environment & Path Resolution
# -------------------------------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = SCRIPT_DIR / "artifacts"

def find_engine_sources() -> Path:
    candidates = [
        Path(r"C:\Users\MAHESH\unvibecode-lab\.venv\Lib\site-packages\shipreadyv2\engine_sources"),
        SCRIPT_DIR.parent / ".venv" / "Lib" / "site-packages" / "shipreadyv2" / "engine_sources",
    ]
    try:
        import shipreadyv2
        candidates.insert(0, Path(shipreadyv2.__file__).parent / "engine_sources")
    except ImportError:
        pass
    
    for c in candidates:
        if c.exists() and (c / "04_shipreadyv2_business_path_compiler.py").exists():
            return c
    raise RuntimeError(
        "Could not find shipreadyv2 engine_sources. Ensure unvibecode==0.3.15 is installed in python env."
    )

ENGINE_DIR = find_engine_sources()
sys.path.insert(0, str(ENGINE_DIR))

import importlib.util

def load_engine_module(name: str, filename: str):
    module_path = ENGINE_DIR / filename
    if not module_path.is_file():
        raise FileNotFoundError(f"Required engine module missing: {module_path}")
    spec = importlib.util.spec_from_file_location(name, str(module_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

step4 = load_engine_module("step4", "04_shipreadyv2_business_path_compiler.py")
step5 = load_engine_module("step5", "05_shipreadyv2_critical_business_insight_selector_v4.py")


def main() -> int:
    print("=" * 80)
    print("UNVIBECODE 0.3.15: SAME_PATH_FRAGMENT FALSE DEDUPLICATION REPRODUCTION")
    print(f"Engine Sources:  {ENGINE_DIR}")
    print(f"Artifacts Dir:   {ARTIFACTS_DIR}")
    print("=" * 80)

    # ---------------------------------------------------------------------------------------------
    # STAGE 1: Extract and Validate Authentic Cypress Artifacts
    # ---------------------------------------------------------------------------------------------
    print("\n[STAGE 1] Validating Authentic Cypress Context Chunks & Connections...")
    chunks_path = ARTIFACTS_DIR / "chunks.jsonl"
    connections_path = ARTIFACTS_DIR / "connections.jsonl"
    review_log_path = ARTIFACTS_DIR / "business_workflow_review.log"

    if not chunks_path.exists() or not connections_path.exists():
        print(f"ERROR: Missing context artifacts in {ARTIFACTS_DIR}")
        return 1

    chunk_helpers = None
    chunk_trans = None
    chunk_notif = None

    with open(chunks_path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            file_name = data.get("file", "")
            if file_name == "backend/helpers.ts":
                chunk_helpers = data["chunk_id"]
            elif file_name == "backend/transaction-routes.ts":
                chunk_trans = data["chunk_id"]
            elif file_name == "backend/notification-routes.ts":
                chunk_notif = data["chunk_id"]

    print(f"  * backend/helpers.ts chunk:              {chunk_helpers}")
    print(f"  * backend/transaction-routes.ts chunk:   {chunk_trans}")
    print(f"  * backend/notification-routes.ts chunk:  {chunk_notif}")

    assert chunk_helpers, "Could not find backend/helpers.ts in real chunks"
    assert chunk_trans, "Could not find backend/transaction-routes.ts in real chunks"
    assert chunk_notif, "Could not find backend/notification-routes.ts in real chunks"

    # Verify cross-file connections to ensureAuthenticated
    verified_connections = []
    with open(connections_path, "r", encoding="utf-8") as f:
        for line in f:
            conn = json.loads(line)
            if conn.get("symbol") == "ensureAuthenticated" and conn.get("target_chunk") == chunk_helpers:
                verified_connections.append(conn)

    print(f"  * Verified routes importing ensureAuthenticated: {len(verified_connections)}")
    for conn in verified_connections:
        print(f"    - {conn['source_file']} -> {conn['target_file']}::ensureAuthenticated (confidence={conn['confidence']})")

    # Parse authentic business path IDs from the actual Cypress run log
    real_paths = []
    if review_log_path.exists():
        log_text = review_log_path.read_text(encoding="utf-8")
        matches = re.findall(r"proving candidates for (business_path_[a-f0-9]+)", log_text)
        real_paths = sorted(set(matches))
        print(f"  * Real path IDs evaluated in completed run: {len(real_paths)}")
        for pid in real_paths:
            print(f"    - {pid}")

    # Use the authentic business paths identified in business_workflow_review.log
    # and published in report-support/business-workflows.html:
    # - business_path_e0050026511ee242: "Create or update transactions" (Workflow Area 1)
    # - business_path_005a3eab6bf1afae: "Create notifications and update notification fields" (Workflow Area 2)
    path_id_1 = "business_path_e0050026511ee242"
    path_id_2 = "business_path_005a3eab6bf1afae"

    assert path_id_1 in real_paths, f"Expected {path_id_1} in real run paths"
    assert path_id_2 in real_paths, f"Expected {path_id_2} in real run paths"
    print(f"  * Verified Path 1 (Area 1: Transactions):  {path_id_1}")
    print(f"  * Verified Path 2 (Area 2: Notifications): {path_id_2}")

    # ---------------------------------------------------------------------------------------------
    # STAGE 2: Execute Actual Step 04 Relationship Compilation
    # ---------------------------------------------------------------------------------------------
    print("\n[STAGE 2] Executing Actual Step 04 (04_shipreadyv2_business_path_compiler.py)...")

    path_transaction = {
        "normalized_path_id": path_id_1,
        "endpoint": {"route": "/transactions", "method": "POST"},
        "entrypoints": [{"repo_native_entrypoint": "POST /transactions"}],
        "effects": [{"effect_classification": {"canonical_value": "DATABASE_WRITE"}}],
        "evidence": [
            {"chunk_id": chunk_trans, "validation_status": "VALID", "evidence_id": "ev_trans_route"},
            {"chunk_id": chunk_helpers, "validation_status": "VALID", "evidence_id": "ev_shared_auth"},
        ],
        "implementation_group_ids": [],
        "canonical_confidence": {"score": 88},
    }

    path_notification = {
        "normalized_path_id": path_id_2,
        "endpoint": {"route": "/notifications", "method": "GET"},
        "entrypoints": [{"repo_native_entrypoint": "GET /notifications"}],
        "effects": [{"effect_classification": {"canonical_value": "DATABASE_READ"}}],
        "evidence": [
            {"chunk_id": chunk_notif, "validation_status": "VALID", "evidence_id": "ev_notif_route"},
            {"chunk_id": chunk_helpers, "validation_status": "VALID", "evidence_id": "ev_shared_auth"},
        ],
        "implementation_group_ids": [],
        "canonical_confidence": {"score": 82},
    }

    class NullAudit:
        def add(self, *args, **kwargs): pass

    groups, relationships = step4.build_implementation_groups(
        [path_transaction, path_notification], NullAudit()
    )

    print(f"  * Relationships produced:  {len(relationships)}")
    print(f"  * Implementation groups:  {len(groups)}")
    for rel in relationships:
        print(f"    - Type:       {rel['relationship']}")
        print(f"    - Rule ID:    {rel['rule_ids']}")
        print(f"    - Source:     {rel['source_path_id']}")
        print(f"    - Target:     {rel['target_path_id']}")
    print(f"  * Transaction implementation_group_ids: {path_transaction['implementation_group_ids']}")
    print(f"  * Notification implementation_group_ids: {path_notification['implementation_group_ids']}")
    print("  => Step 04 explicitly did NOT assign implementation_group_ids, because sharing a helper")
    print("     (SAME_PATH_FRAGMENT) is structurally distinct from being duplicate implementations.")

    # ---------------------------------------------------------------------------------------------
    # STAGE 3: Execute Actual Step 05 Deduplication: Baseline vs Fixed
    # ---------------------------------------------------------------------------------------------
    print("\n[STAGE 3] Executing Actual Step 05 Deduplication (Baseline A vs Fixed B)...")

    # Both routes receive caller HTTP requests and execute business logic,
    # qualifying for Step 05's canonical CROSS_BOUNDARY_TRUST_PATH family
    candidate_trans = {
        "insight_id": "insight_trans_cross_boundary",
        "family": "CROSS_BOUNDARY_TRUST_PATH",
        "title": "Cross-boundary trust boundary risk (/transactions)",
        "normalized_path_ids": [path_transaction["normalized_path_id"]],
        "implementation_group_ids": list(path_transaction["implementation_group_ids"]),
        "decision": "ELIGIBLE_STRONG",
        "qualification_status": "ELIGIBLE",
        "rejection_reasons": [],
        "score": {"total": 92},
        "confidence": {"candidate": 90},
    }

    candidate_notif = {
        "insight_id": "insight_notif_cross_boundary",
        "family": "CROSS_BOUNDARY_TRUST_PATH",
        "title": "Cross-boundary trust boundary risk (/notifications)",
        "normalized_path_ids": [path_notification["normalized_path_id"]],
        "implementation_group_ids": list(path_notification["implementation_group_ids"]),
        "decision": "ELIGIBLE_STRONG",
        "qualification_status": "ELIGIBLE",
        "rejection_reasons": [],
        "score": {"total": 85},
        "confidence": {"candidate": 85},
    }

    normalized_data = {"path_relationships": relationships}

    # --- Run Baseline A (Unmodified Step 05) ---
    baseline_candidates = [copy.deepcopy(candidate_trans), copy.deepcopy(candidate_notif)]
    step5.deduplicate_candidates(baseline_candidates, normalized_data)

    print("\n  [BASELINE A: UnvibeCode 0.3.15 Actual Logic]")
    for c in baseline_candidates:
        print(f"    * [{c['insight_id']}] Decision: {c['decision']} | Status: {c['qualification_status']}")
        for r in c.get("rejection_reasons", []):
            print(f"      -> Rejection: [{r['code']}] {r['reason']}")

    # --- Run Experiment B (Fixed Grouping Fallback) ---
    fixed_candidates = [copy.deepcopy(candidate_trans), copy.deepcopy(candidate_notif)]

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

    fixed_deduplicate_candidates(fixed_candidates, normalized_data)

    print("\n  [EXPERIMENT B: Fixed Grouping Fallback]")
    for c in fixed_candidates:
        print(f"    * [{c['insight_id']}] Decision: {c['decision']} | Status: {c['qualification_status']}")

    # ---------------------------------------------------------------------------------------------
    # STAGE 4: Comparison & Machine-Readable Report
    # ---------------------------------------------------------------------------------------------
    baseline_trans = next(c for c in baseline_candidates if c["insight_id"] == candidate_trans["insight_id"])
    baseline_notif = next(c for c in baseline_candidates if c["insight_id"] == candidate_notif["insight_id"])

    fixed_trans = next(c for c in fixed_candidates if c["insight_id"] == candidate_trans["insight_id"])
    fixed_notif = next(c for c in fixed_candidates if c["insight_id"] == candidate_notif["insight_id"])

    bug_confirmed = (
        baseline_trans["decision"] == "ELIGIBLE_STRONG"
        and baseline_notif["decision"] == "DUPLICATE_OR_VARIANT"
        and fixed_trans["decision"] == "ELIGIBLE_STRONG"
        and fixed_notif["decision"] == "ELIGIBLE_STRONG"
    )

    results_payload = {
        "repository": "cypress-realworld-app",
        "shared_helper_chunk": chunk_helpers,
        "path_1": {
            "id": path_id_1,
            "title": "Create or update transactions",
            "area": "Transaction workflows",
        },
        "path_2": {
            "id": path_id_2,
            "title": "Create notifications and update notification fields",
            "area": "Create notifications and update notification fields",
        },
        "relationship_produced": relationships[0]["relationship"] if relationships else None,
        "baseline": {
            "transaction_candidate_decision": baseline_trans["decision"],
            "notification_candidate_decision": baseline_notif["decision"],
            "notification_rejection_reasons": baseline_notif.get("rejection_reasons", []),
        },
        "fixed": {
            "transaction_candidate_decision": fixed_trans["decision"],
            "notification_candidate_decision": fixed_notif["decision"],
        },
        "defect_reproduced_and_verified": bug_confirmed,
    }

    out_file = SCRIPT_DIR / "reproduction_results.json"
    out_file.write_text(json.dumps(results_payload, indent=2), encoding="utf-8")
    print(f"\n[REPORT WRITTEN] Machine-readable results saved to: {out_file}")

    print("\n" + "=" * 80)
    if bug_confirmed:
        print(">>> RESULT: MECHANISM DEFECT REPRODUCED DETERMINISTICALLY <<<")
        print("  SAME_PATH_FRAGMENT deduplication behavior reproduced deterministically using")
        print("  actual UnvibeCode 0.3.15 Step 04 and Step 05 functions with constructed candidate")
        print("  fixtures and authentic Cypress repository-context evidence.")
        print("  Note: End-to-end candidate suppression in the completed Cypress analysis")
        print("  remains to be independently verified once raw candidate artifacts are captured.")
        print("=" * 80)
        return 0
    else:
        print(">>> RESULT: Defect condition not satisfied. <<<")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    sys.exit(main())
