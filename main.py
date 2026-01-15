import json
import argparse
from datetime import datetime
from pathlib import Path
from src.debate.debate_system import DebateSystem
from config.settings import PROBLEMS_FILE, RESULTS_DIR


def load_problems():
    """Load problems from JSON file"""
    with open(PROBLEMS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_result(result: dict, problem_id: int):
    """Save individual result to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"problem_{problem_id}_{timestamp}.json"
    filepath = Path(RESULTS_DIR) / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\nResult saved to: {filepath}")


def run_single_problem(problem_id: int):
    """Run debate on a single problem"""
    problems = load_problems()
    problem = next((p for p in problems if p["id"] == problem_id), None)
    
    if not problem:
        print(f"Problem {problem_id} not found!")
        return
    
    system = DebateSystem()
    result = system.run_debate(problem)
    save_result(result, problem_id)
    
    print("\n" + "="*60)
    print("FINAL JUDGMENT:")
    print("="*60)
    print(result["judgment"])


def run_all_problems():
    """Run debate on all problems"""
    problems = load_problems()
    system = DebateSystem()
    
    # Check which problems are already completed
    completed_ids = set()
    for file in Path(RESULTS_DIR).glob("problem_*.json"):
        # Extract problem ID from filename
        try:
            problem_id = int(file.stem.split('_')[1])
            completed_ids.add(problem_id)
        except:
            pass
    
    print(f"\n{'='*60}")
    print(f"Already completed: {len(completed_ids)} problems")
    print(f"Remaining: {len(problems) - len(completed_ids)} problems")
    print(f"{'='*60}\n")
    
    all_results = []
    
    for problem in problems:
        # Skip if already completed
        if problem['id'] in completed_ids:
            print(f"⏭️  Skipping Problem {problem['id']} (already completed)")
            continue
            
        try:
            result = system.run_debate(problem)
            save_result(result, problem["id"])
            all_results.append(result)
        except Exception as e:
            print(f"\n❌ Error on Problem {problem['id']}: {e}")
            print("Saving progress and continuing...")
            continue
    
    # Save summary
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = Path(RESULTS_DIR) / f"summary_{timestamp}.json"
    
    if all_results:
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n\n{'='*60}")
    print(f"✅ Batch complete!")
    print(f"Total completed: {len(completed_ids) + len(all_results)} / {len(problems)}")
    print(f"{'='*60}")
    if all_results:
        print(f"Summary: {summary_file}")


def main():
    parser = argparse.ArgumentParser(description="Multi-LLM Debate System")
    parser.add_argument(
        "--problem-id", 
        type=int, 
        help="Run on specific problem ID"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run on all problems"
    )
    
    args = parser.parse_args()
    
    if args.problem_id is not None:
        run_single_problem(args.problem_id)
    elif args.all:
        run_all_problems()
    else:
        # Default: run on first problem
        print("No arguments provided. Running on problem 0 as test...")
        print("Use --problem-id N or --all for full runs")
        run_single_problem(0)


if __name__ == "__main__":
    main()