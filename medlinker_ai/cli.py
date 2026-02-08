"""Command-line interface for MedLinker AI."""

import sys
import json
from pathlib import Path

from medlinker_ai.models import FacilityDocInput, FacilityAnalysisOutput
from medlinker_ai.extract import extract_capabilities
from medlinker_ai.verify import verify_facility
from medlinker_ai.dataset import load_facility_docs_from_csv
from medlinker_ai.aggregate import aggregate_regions
from medlinker_ai.qa import answer_planner_question
from medlinker_ai.trace import get_trace, list_recent_traces


def extract_command(input_path: str) -> None:
    """Extract capabilities from facility input JSON.
    
    Args:
        input_path: Path to facility input JSON file.
    """
    # Load input
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    with open(input_file) as f:
        input_data = json.load(f)
    
    # Parse input
    try:
        doc = FacilityDocInput(**input_data)
    except Exception as e:
        print(f"Error: Invalid input format: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Extract capabilities
    try:
        capabilities, citations = extract_capabilities(doc)
    except Exception as e:
        print(f"Error: Extraction failed: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Build output
    output = {
        "facility_id": doc.facility_id,
        "extracted_capabilities": capabilities.model_dump(),
        "citations": [c.model_dump() for c in citations]
    }
    
    # Print JSON output
    print(json.dumps(output, indent=2))


def verify_command(input_path: str) -> None:
    """Verify facility capabilities and detect inconsistencies.
    
    Args:
        input_path: Path to facility input JSON file.
    """
    # Load input
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    with open(input_file) as f:
        input_data = json.load(f)
    
    # Parse input
    try:
        doc = FacilityDocInput(**input_data)
    except Exception as e:
        print(f"Error: Invalid input format: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Verify facility
    try:
        analysis = verify_facility(doc)
    except Exception as e:
        print(f"Error: Verification failed: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Print JSON output
    print(json.dumps(analysis.model_dump(), indent=2))


def run_dataset_command(csv_path: str, limit: int = None) -> None:
    """Run verification on dataset and output JSONL.
    
    Args:
        csv_path: Path to CSV file
        limit: Optional limit on number of rows
    """
    # Load facilities from CSV
    print(f"Loading facilities from {csv_path}...", file=sys.stderr)
    facilities = load_facility_docs_from_csv(csv_path, limit=limit)
    print(f"Loaded {len(facilities)} facilities", file=sys.stderr)
    
    # Create output directory
    output_dir = Path("./outputs")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "facilities.jsonl"
    
    # Process each facility
    print(f"Processing facilities...", file=sys.stderr)
    with open(output_file, 'w') as f:
        for i, doc in enumerate(facilities, 1):
            try:
                analysis = verify_facility(doc)
                f.write(json.dumps(analysis.model_dump()) + "\n")
                
                if i % 10 == 0:
                    print(f"  Processed {i}/{len(facilities)}", file=sys.stderr)
            except Exception as e:
                print(f"  Error processing {doc.facility_id}: {e}", file=sys.stderr)
    
    print(f"\nOutput written to {output_file}", file=sys.stderr)
    print(f"Processed {len(facilities)} facilities", file=sys.stderr)


def aggregate_command(jsonl_path: str) -> None:
    """Aggregate facilities into regional summaries.
    
    Args:
        jsonl_path: Path to JSONL file with facility outputs
    """
    # Load facility outputs
    print(f"Loading facility outputs from {jsonl_path}...", file=sys.stderr)
    facility_outputs = []
    
    with open(jsonl_path, 'r') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                output = FacilityAnalysisOutput(**data)
                facility_outputs.append(output)
    
    print(f"Loaded {len(facility_outputs)} facility outputs", file=sys.stderr)
    
    # Aggregate by region
    print("Aggregating by region...", file=sys.stderr)
    summaries = aggregate_regions(facility_outputs)
    
    # Write output
    output_dir = Path("./outputs")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "regions.json"
    
    with open(output_file, 'w') as f:
        json.dump([s.model_dump() for s in summaries], f, indent=2)
    
    print(f"\nOutput written to {output_file}", file=sys.stderr)
    print(f"Aggregated {len(summaries)} regions", file=sys.stderr)
    
    # Print top 5 regions by desert score
    print("\nTop 5 Medical Desert Regions:", file=sys.stderr)
    for i, summary in enumerate(summaries[:5], 1):
        print(f"{i}. {summary.country}-{summary.region}: Score {summary.desert_score}", file=sys.stderr)
        print(f"   Missing: {', '.join(summary.missing_critical[:3])}", file=sys.stderr)


def ask_command(facilities_path: str, regions_path: str, question: str) -> None:
    """Answer planner question using facility and region data.
    
    Args:
        facilities_path: Path to facilities JSONL file
        regions_path: Path to regions JSON file
        question: User question
    """
    # Load facilities
    print(f"Loading facilities from {facilities_path}...", file=sys.stderr)
    facilities = []
    with open(facilities_path, 'r') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                facilities.append(FacilityAnalysisOutput(**data))
    
    # Load regions
    print(f"Loading regions from {regions_path}...", file=sys.stderr)
    with open(regions_path, 'r') as f:
        regions_data = json.load(f)
    
    from medlinker_ai.models import RegionSummary
    regions = [RegionSummary(**r) for r in regions_data]
    
    print(f"Loaded {len(facilities)} facilities, {len(regions)} regions", file=sys.stderr)
    
    # Answer question
    print(f"\nQuestion: {question}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    result = answer_planner_question(question, facilities, regions)
    
    # Print answer
    print("\nAnswer:", file=sys.stderr)
    print(result["answer"])
    
    # Print citations (compact)
    if result["citations"]:
        print(f"\nCitations ({len(result['citations'])}):", file=sys.stderr)
        for i, citation in enumerate(result["citations"][:5], 1):
            snippet = citation["snippet"]
            if len(snippet) > 80:
                snippet = snippet[:77] + "..."
            print(f"  {i}. {citation['field']}: {snippet}", file=sys.stderr)
        
        if len(result["citations"]) > 5:
            print(f"  ... and {len(result['citations']) - 5} more", file=sys.stderr)
    
    print(f"\nTrace ID: {result['trace_id']}", file=sys.stderr)


def trace_show_command(trace_id: str) -> None:
    """Show details of a specific trace.
    
    Args:
        trace_id: Trace identifier
    """
    trace = get_trace(trace_id)
    
    if not trace:
        print(f"Error: Trace not found: {trace_id}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Trace ID: {trace.trace_id}")
    print(f"Steps: {len(trace.spans)}")
    print("=" * 60)
    
    for i, span in enumerate(trace.spans, 1):
        print(f"\n{i}. Step: {span.step_name}")
        print(f"   Timestamp: {span.timestamp}")
        print(f"   Inputs: {json.dumps(span.inputs_summary, indent=6)}")
        print(f"   Outputs: {json.dumps(span.outputs_summary, indent=6)}")
        print(f"   Evidence refs: {span.evidence_refs}")


def trace_list_command(limit: int = 10) -> None:
    """List recent traces.
    
    Args:
        limit: Maximum number of traces to show
    """
    trace_ids = list_recent_traces(limit=limit)
    
    if not trace_ids:
        print("No traces found", file=sys.stderr)
        return
    
    print(f"Recent traces (last {len(trace_ids)}):")
    print("=" * 60)
    
    for i, trace_id in enumerate(trace_ids, 1):
        trace = get_trace(trace_id)
        if trace:
            steps = ", ".join([s.step_name for s in trace.spans])
            print(f"{i}. {trace_id}")
            print(f"   Steps: {steps}")
        else:
            print(f"{i}. {trace_id} (details unavailable)")


def main() -> None:
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m medlinker_ai.cli <command> [args]", file=sys.stderr)
        print("\nCommands:", file=sys.stderr)
        print("  extract <input.json>                    - Extract capabilities from facility input", file=sys.stderr)
        print("  verify <input.json>                     - Verify facility and detect inconsistencies", file=sys.stderr)
        print("  run_dataset <csv> [--limit N]           - Run verification on dataset", file=sys.stderr)
        print("  aggregate <jsonl>                       - Aggregate facilities into regional summaries", file=sys.stderr)
        print("  ask <facilities.jsonl> <regions.json> <question>  - Answer planner question", file=sys.stderr)
        print("  trace show <trace_id>                   - Show details of a specific trace", file=sys.stderr)
        print("  trace list [--limit N]                  - List recent traces", file=sys.stderr)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "extract":
        if len(sys.argv) < 3:
            print("Usage: python -m medlinker_ai.cli extract <input.json>", file=sys.stderr)
            sys.exit(1)
        extract_command(sys.argv[2])
    elif command == "verify":
        if len(sys.argv) < 3:
            print("Usage: python -m medlinker_ai.cli verify <input.json>", file=sys.stderr)
            sys.exit(1)
        verify_command(sys.argv[2])
    elif command == "run_dataset":
        if len(sys.argv) < 3:
            print("Usage: python -m medlinker_ai.cli run_dataset <csv> [--limit N]", file=sys.stderr)
            sys.exit(1)
        
        csv_path = sys.argv[2]
        limit = None
        
        # Parse --limit flag
        if len(sys.argv) > 3 and sys.argv[3] == "--limit" and len(sys.argv) > 4:
            try:
                limit = int(sys.argv[4])
            except ValueError:
                print("Error: --limit must be an integer", file=sys.stderr)
                sys.exit(1)
        
        run_dataset_command(csv_path, limit=limit)
    elif command == "aggregate":
        if len(sys.argv) < 3:
            print("Usage: python -m medlinker_ai.cli aggregate <jsonl>", file=sys.stderr)
            sys.exit(1)
        aggregate_command(sys.argv[2])
    elif command == "ask":
        if len(sys.argv) < 5:
            print("Usage: python -m medlinker_ai.cli ask <facilities.jsonl> <regions.json> <question>", file=sys.stderr)
            sys.exit(1)
        ask_command(sys.argv[2], sys.argv[3], sys.argv[4])
    elif command == "trace":
        if len(sys.argv) < 3:
            print("Usage: python -m medlinker_ai.cli trace <show|list> [args]", file=sys.stderr)
            sys.exit(1)
        
        subcommand = sys.argv[2]
        
        if subcommand == "show":
            if len(sys.argv) < 4:
                print("Usage: python -m medlinker_ai.cli trace show <trace_id>", file=sys.stderr)
                sys.exit(1)
            trace_show_command(sys.argv[3])
        elif subcommand == "list":
            limit = 10
            if len(sys.argv) > 3 and sys.argv[3] == "--limit" and len(sys.argv) > 4:
                try:
                    limit = int(sys.argv[4])
                except ValueError:
                    print("Error: --limit must be an integer", file=sys.stderr)
                    sys.exit(1)
            trace_list_command(limit=limit)
        else:
            print(f"Error: Unknown trace subcommand: {subcommand}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Error: Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
