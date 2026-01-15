"""Quick test script to verify evaluation is working"""
import json
from pathlib import Path
from src.evaluation.metrics import DebateEvaluator

def main():
    print("=" * 60)
    print("Testing Evaluation System")
    print("=" * 60)
    
    # Check what files exist
    results_dir = Path("data/results")
    result_files = list(results_dir.glob("problem_*.json"))
    
    print(f"\nFound {len(result_files)} result files:")
    for f in sorted(result_files)[:5]:  # Show first 5
        print(f"  - {f.name}")
    if len(result_files) > 5:
        print(f"  ... and {len(result_files) - 5} more")
    
    # Try loading results
    print("\n" + "=" * 60)
    print("Loading results...")
    print("=" * 60)
    
    evaluator = DebateEvaluator()
    results = evaluator.load_results()
    
    print(f"\nSuccessfully loaded: {len(results)} results")
    
    if results:
        # Show sample result
        print("\nSample result structure:")
        sample = results[0]
        print(f"  Problem ID: {sample.get('problem', {}).get('id', 'N/A')}")
        print(f"  Question: {sample.get('problem', {}).get('question', 'N/A')[:60]}...")
        print(f"  Has judgment: {bool(sample.get('judgment'))}")
        
        # Calculate metrics
        print("\n" + "=" * 60)
        print("Calculating metrics...")
        print("=" * 60)
        
        metrics = evaluator.calculate_metrics(results)
        
        print(f"\n📊 RESULTS:")
        print(f"  Total Problems: {metrics['total_problems']}")
        print(f"  Correct Answers: {metrics['correct_answers']}")
        print(f"  Accuracy: {metrics['accuracy']*100:.2f}%")
        
        # Show which problems were correct
        print(f"\n✅ Correct problems:")
        for result in results:
            problem = result.get('problem', {})
            if evaluator.check_correctness(result, problem):
                print(f"  - Problem {problem.get('id')}: {problem.get('question', '')[:50]}...")
        
        print(f"\n❌ Incorrect problems:")
        for result in results:
            problem = result.get('problem', {})
            if not evaluator.check_correctness(result, problem):
                print(f"  - Problem {problem.get('id')}: {problem.get('question', '')[:50]}...")
                expected = problem.get('correct_answer', 'N/A')
                judgment = result.get('judgment', '')
                extracted = evaluator.extract_answer(judgment)
                print(f"    Expected: {expected}")
                print(f"    Got: {extracted[:100]}")
    else:
        print("\n⚠️  No results loaded!")
        print("\nTroubleshooting:")
        print("1. Make sure you've run: python main.py --all")
        print("2. Check that files exist in data/results/")
        print("3. Verify file names match pattern: problem_*_*.json")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()