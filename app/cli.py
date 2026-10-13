"""Command Line Interface for LedgerLens.
Supports:
  app run [--sample <dir> | --file <file>]
  app update [--all | models | prompts | schema]
  app eval [--report <path>]
  app purge (delete all user data)
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import List

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.core.pipeline import get_pipeline
from app.core.output import export_documents_to_csv, export_documents_to_json, generate_printable_summary_markdown
from app.update.orchestrator import get_orchestrator
from app.update.prompts import PromptUpdater
from app.store.db import get_db
from app.config import get_config
from app.utils.logging import logger
from evals.run import run_evaluation

def handle_run(args: argparse.Namespace) -> None:
    pipeline = get_pipeline()
    files_to_process: List[Path] = []

    if args.sample:
        sample_path = Path(args.sample)
        if sample_path.is_dir():
            for ext in ("*.png", "*.jpg", "*.jpeg", "*.pdf", "*.txt"):
                files_to_process.extend(sample_path.glob(ext))
        elif sample_path.is_file():
            files_to_process.append(sample_path)
    elif args.file:
        files_to_process.append(Path(args.file))
    else:
        print("Please provide --sample <dir> or --file <path>")
        sys.exit(1)

    if not files_to_process:
        print(f"No documents found to process in {args.sample or args.file}")
        sys.exit(0)

    print(f"-> Processing {len(files_to_process)} documents locally...")
    results = pipeline.process_batch(files_to_process)

    # Output summaries
    summary_md = generate_printable_summary_markdown(results)
    print("\n" + summary_md + "\n")

    if args.out_csv:
        export_documents_to_csv(results, target_file=args.out_csv)
        print(f"Saved CSV export to: {args.out_csv}")
    if args.out_json:
        export_documents_to_json(results, target_file=args.out_json)
        print(f"Saved JSON export to: {args.out_json}")

def handle_update(args: argparse.Namespace) -> None:
    orchestrator = get_orchestrator()
    if args.all or (not args.models and not args.prompts and not args.schema):
        orchestrator.update_all()
    elif args.models:
        orchestrator.model_updater.update_models()
    elif args.prompts:
        orchestrator.prompt_updater.evaluate_and_promote("extract_fields", "v2")
    elif args.schema:
        orchestrator.schema_updater.run_migrations()

def handle_eval(args: argparse.Namespace) -> None:
    report_file = Path(args.report) if args.report else None
    result = run_evaluation(report_file=report_file)
    if result["metrics"]["overall_exact_match"] < 0.85:
        sys.exit(1)
    sys.exit(0)

def handle_purge(args: argparse.Namespace) -> None:
    if not args.yes:
        confirm = input("Are you sure you want to PERMANENTLY delete all local user data? (yes/no): ")
        if confirm.lower() != "yes":
            print("Purge cancelled.")
            return
    db = get_db()
    db.purge_all_data()
    print("[OK] All user documents, line items, and corrections have been permanently deleted.")

def main() -> None:
    parser = argparse.ArgumentParser(prog="app", description="LedgerLens Local CLI")
    subparsers = parser.add_subparsers(dest="command")

    # run
    p_run = subparsers.add_parser("run", help="Process receipts and invoices")
    p_run.add_argument("--sample", type=str, help="Directory containing sample images/PDFs")
    p_run.add_argument("--file", type=str, help="Single file to process")
    p_run.add_argument("--out-csv", type=str, help="Optional output CSV path")
    p_run.add_argument("--out-json", type=str, help="Optional output JSON path")

    # update
    p_update = subparsers.add_parser("update", help="Run auto-update channels")
    p_update.add_argument("--all", action="store_true", help="Run all 5 update channels")
    p_update.add_argument("--models", action="store_true", help="Update models only")
    p_update.add_argument("--prompts", action="store_true", help="Update and eval prompts only")
    p_update.add_argument("--schema", action="store_true", help="Run migrations only")

    # eval
    p_eval = subparsers.add_parser("eval", help="Run evaluation against golden set")
    p_eval.add_argument("--report", type=str, help="Report destination file")

    # purge
    p_purge = subparsers.add_parser("purge", help="Delete all local user data")
    p_purge.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")

    args = parser.parse_args()
    if args.command == "run":
        handle_run(args)
    elif args.command == "update":
        handle_update(args)
    elif args.command == "eval":
        handle_eval(args)
    elif args.command == "purge":
        handle_purge(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
