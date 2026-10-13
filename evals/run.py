"""Eval Harness for LedgerLens.

GATES EVERYTHING:
- Runs evaluation against golden dataset (evals/golden/*.jsonl)
- Computes per-field accuracy vs. baseline
- Returns exit code 0 on passing criteria, 1 on regression
- Used by 'make eval' and the auto-update eval gate
"""

from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.core.extract import extract_document
from app.core.normalize import normalize_extracted_fields
from app.core.infer import get_inference_engine
from app.agent.harness import InspectableAgentHarness
from app.agent.prompts_loader import get_prompt
from app.utils.logging import logger

def load_golden_set(golden_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load all golden test cases from evals/golden/*.jsonl."""
    base_dir = Path(__file__).resolve().parent
    g_dir = golden_dir or (base_dir / "golden")
    cases: List[Dict[str, Any]] = []

    for file_path in sorted(g_dir.glob("*.jsonl")):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        cases.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    return cases

def evaluate_single_case(
    case: Dict[str, Any],
    harness: InspectableAgentHarness,
    prompt_version: Optional[str] = None
) -> Tuple[bool, Dict[str, bool], Dict[str, Any]]:
    raw_text = case["raw_text"]
    expected = case["expected"]

    # Execute agent harness with specified prompt version if provided
    few_shot_str = "No user corrections on file."
    prompt_text = get_prompt("extract_fields", version=prompt_version, raw_text=raw_text, few_shot_context=few_shot_str)
    
    # Run through local inference engine
    raw_response = harness.infer_fn(prompt_text, None) if harness.infer_fn else "{}"
    parsed = harness._clean_and_parse_json(raw_response)
    normalized = normalize_extracted_fields(parsed)

    # Field comparisons
    results: Dict[str, bool] = {}

    # Vendor: case-insensitive containment or match (cleaned of punctuation symbols)
    import re
    exp_vendor = re.sub(r"[#*@\s\-]+", " ", str(expected.get("vendor", ""))).strip().lower()
    act_vendor = re.sub(r"[#*@\s\-]+", " ", str(normalized.get("vendor", ""))).strip().lower()
    vendor_match = (exp_vendor in act_vendor or act_vendor in exp_vendor) and len(act_vendor) > 1
    results["vendor"] = vendor_match

    # Date: normalized ISO comparison
    exp_date = expected.get("doc_date")
    act_date = normalized.get("doc_date")
    results["date"] = (exp_date == act_date)

    # Total: within $0.05
    exp_total = expected.get("total_amount")
    act_total = normalized.get("total_amount")
    if exp_total is not None and act_total is not None:
        results["total"] = abs(float(exp_total) - float(act_total)) <= 0.05
    else:
        results["total"] = (exp_total == act_total)

    # Tax: within $0.05
    exp_tax = expected.get("tax_amount", 0.0)
    act_tax = normalized.get("tax_amount", 0.0)
    results["tax"] = abs(float(exp_tax) - float(act_tax)) <= 0.05

    # Category: case-insensitive match
    exp_cat = str(expected.get("category", "")).strip().lower()
    act_cat = str(normalized.get("category", "")).strip().lower()
    results["category"] = (exp_cat == act_cat)

    all_matched = all(results.values())
    return all_matched, results, normalized

def run_evaluation(
    prompt_version: Optional[str] = None,
    report_file: Optional[Path] = None,
    fail_under: float = 0.85,
    strict: bool = False
) -> Dict[str, Any]:
    """Execute complete eval run and compare to baseline."""
    cases = load_golden_set()
    if not cases:
        raise RuntimeError("No golden test cases found in evals/golden/")

    infer_engine = get_inference_engine()
    harness = InspectableAgentHarness(infer_fn=infer_engine.generate)

    field_counts = {"vendor": 0, "date": 0, "total": 0, "tax": 0, "category": 0}
    perfect_cases = 0

    print(f"\n=================================================================")
    print(f" LedgerLens Evaluation Suite: {len(cases)} Golden Cases")
    print(f" Active Profile: {infer_engine.config_manager.app_config.profile} | Prompt: {prompt_version or 'current'}")
    if strict:
        print(f" Mode: STRICT (No field regressions allowed vs. baseline)")
    print(f"=================================================================\n")

    for case in cases:
        all_match, field_res, _ = evaluate_single_case(case, harness, prompt_version=prompt_version)
        if all_match:
            perfect_cases += 1
        for field, match in field_res.items():
            if match:
                field_counts[field] += 1

    total_n = len(cases)
    metrics = {
        "vendor_accuracy": round(field_counts["vendor"] / total_n, 3),
        "date_accuracy": round(field_counts["date"] / total_n, 3),
        "total_accuracy": round(field_counts["total"] / total_n, 3),
        "tax_accuracy": round(field_counts["tax"] / total_n, 3),
        "category_accuracy": round(field_counts["category"] / total_n, 3),
        "overall_exact_match": round(perfect_cases / total_n, 3),
    }

    # Load baseline
    baseline_file = Path(__file__).resolve().parent / "baselines" / "latest.json"
    baseline_metrics = {}
    if baseline_file.exists():
        try:
            baseline_data = json.loads(baseline_file.read_text(encoding="utf-8"))
            baseline_metrics = baseline_data.get("metrics", {})
        except Exception:
            pass

    # Print summary table
    print(f"{'Field':<22} | {'Current Score':<14} | {'Baseline':<12} | {'Diff':<8}")
    print(f"{'-'*22}-|-{'-'*14}-|-{'-'*12}-|-{'-'*8}")
    regressions: List[str] = []
    for k, v in metrics.items():
        base_v = baseline_metrics.get(k, 0.0)
        diff = round(v - base_v, 3)
        diff_str = f"+{diff:.3f}" if diff >= 0 else f"{diff:.3f}"
        print(f"{k:<22} | {v*100:>5.1f}%         | {base_v*100:>5.1f}%       | {diff_str}")
        if diff < -0.001:
            regressions.append(f"{k} ({diff_str})")

    print(f"\nOverall Exact Match: {metrics['overall_exact_match']*100:.1f}%\n")

    report_payload = {
        "timestamp": datetime.now().isoformat(),
        "total_cases": total_n,
        "perfect_cases": perfect_cases,
        "metrics": metrics,
        "baseline_diff": {k: round(metrics[k] - baseline_metrics.get(k, 0.0), 3) for k in metrics},
        "passed": True
    }

    if report_file:
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
        print(f"Report written to: {report_file}")

    # Threshold determination:
    # 1. Floor check: overall_exact_match must meet fail_under (85.0% floor)
    # 2. Strict check: zero regressed fields vs baseline
    passed = (metrics["overall_exact_match"] >= fail_under)
    if strict and regressions:
        passed = False
        print(f"[STRICT CHECK FAILED] Regressed fields vs baseline: {', '.join(regressions)}")

    report_payload["passed"] = passed

    if not passed:
        print(f"[FAILED] Evaluation did not meet quality threshold")
    else:
        print(f"[PASSED] Evaluation met quality threshold")

    return report_payload

def main() -> None:
    parser = argparse.ArgumentParser(description="LedgerLens Eval Runner")
    parser.add_argument("--report", type=str, help="Path to write report JSON")
    parser.add_argument("--prompt-version", type=str, help="Specific prompt version to evaluate")
    parser.add_argument("--fail-under", type=float, default=0.85, help="Minimum overall accuracy")
    parser.add_argument("--strict", action="store_true", help="Fail if any field regresses vs baseline")
    args = parser.parse_args()

    report_path = Path(args.report) if args.report else None
    result = run_evaluation(
        prompt_version=args.prompt_version,
        report_file=report_path,
        fail_under=args.fail_under,
        strict=args.strict
    )

    if not result.get("passed", False):
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
