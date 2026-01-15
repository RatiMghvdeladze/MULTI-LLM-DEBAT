"""
Baseline Comparison Script
Compares debate system against simpler baselines
"""
import json
from pathlib import Path
from src.models.gemini_wrapper import GeminiWrapper
from config.settings import PROBLEMS_FILE
import time


def load_problems():
    """Load problems from JSON file"""
    with open(PROBLEMS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def single_llm_baseline(problems, max_problems=5):
    """
    Baseline 1: Just ask Gemini once per problem
    (Run on subset to save API calls)
    """
    print("\n" + "="*60)
    print("BASELINE 1: Single LLM (No Debate)")
    print("="*60)
    
    model = GeminiWrapper()
    correct = 0
    
    for i, problem in enumerate(problems[:max_problems]):
        print(f"\nProblem {problem['id']}: {problem['question'][:60]}...")
        
        prompt = f"""Problem: {problem['question']}

Provide your answer clearly. If it's a numerical answer, state it explicitly.

Your answer:"""
        
        try:
            response = model.generate(
                prompt=prompt,
                temperature=0.7,
                top_p=0.9
            )
            
            # Simple check if correct answer is in response
            correct_answer = str(problem['correct_answer']).lower()
            response_lower = response.lower()
            
            is_correct = correct_answer in response_lower
            if is_correct:
                correct += 1
                print(f"  ✅ Correct!")
            else:
                print(f"  ❌ Incorrect")
                print(f"     Expected: {problem['correct_answer']}")
                print(f"     Got: {response[:100]}...")
                
        except Exception as e:
            print(f"  ⚠️ Error: {e}")
            
        time.sleep(2)  # Rate limiting
    
    accuracy = correct / max_problems if max_problems > 0 else 0
    print(f"\n📊 Single LLM Accuracy: {accuracy*100:.1f}% ({correct}/{max_problems})")
    return accuracy


def simple_voting_baseline(problems, max_problems=5):
    """
    Baseline 2: Ask 3 times, pick majority answer
    (Run on subset to save API calls)
    """
    print("\n" + "="*60)
    print("BASELINE 2: Simple Voting (3 Solvers, No Refinement)")
    print("="*60)
    
    model = GeminiWrapper()
    correct = 0
    
    for problem in problems[:max_problems]:
        print(f"\nProblem {problem['id']}: {problem['question'][:60]}...")
        
        prompt = f"""Problem: {problem['question']}

Provide your answer clearly and concisely.

Your answer:"""
        
        # Get 3 independent answers
        answers = []
        for solver_num in range(3):
            try:
                response = model.generate(
                    prompt=prompt,
                    temperature=0.7 + solver_num * 0.1,  # Slight variation
                    top_p=0.9
                )
                answers.append(response)
                time.sleep(2)  # Rate limiting
            except Exception as e:
                print(f"  ⚠️ Solver {solver_num+1} error: {e}")
                answers.append("")
        
        # Simple majority voting (check if 2+ answers contain correct answer)
        correct_answer = str(problem['correct_answer']).lower()
        matches = sum(1 for ans in answers if correct_answer in ans.lower())
        
        is_correct = matches >= 2
        if is_correct:
            correct += 1
            print(f"  ✅ Correct! ({matches}/3 solvers got it)")
        else:
            print(f"  ❌ Incorrect ({matches}/3 solvers got it)")
    
    accuracy = correct / max_problems if max_problems > 0 else 0
    print(f"\n📊 Voting Baseline Accuracy: {accuracy*100:.1f}% ({correct}/{max_problems})")
    return accuracy


def compare_all_systems():
    """Compare debate system with baselines"""
    print("\n" + "="*60)
    print("MULTI-LLM DEBATE SYSTEM - BASELINE COMPARISON")
    print("="*60)
    
    problems = load_problems()
    
    # Run baselines (on subset to save API calls)
    single_accuracy = single_llm_baseline(problems, max_problems=5)
    voting_accuracy = simple_voting_baseline(problems, max_problems=5)
    
    # Load debate system results
    from src.evaluation.metrics import DebateEvaluator
    evaluator = DebateEvaluator()
    results = evaluator.load_results()
    metrics = evaluator.calculate_metrics(results)
    debate_accuracy = metrics['accuracy']
    
    # Print comparison
    print("\n" + "="*60)
    print("FINAL COMPARISON")
    print("="*60)
    print(f"\n1. Single LLM Baseline:      {single_accuracy*100:>6.1f}%")
    print(f"2. Simple Voting Baseline:   {voting_accuracy*100:>6.1f}%")
    print(f"3. Debate System (Full):     {debate_accuracy*100:>6.1f}% ⭐")
    
    improvement_vs_single = ((debate_accuracy - single_accuracy) / single_accuracy * 100) if single_accuracy > 0 else 0
    improvement_vs_voting = ((debate_accuracy - voting_accuracy) / voting_accuracy * 100) if voting_accuracy > 0 else 0
    
    print(f"\nImprovement over Single LLM:  {improvement_vs_single:>+6.1f}%")
    print(f"Improvement over Voting:      {improvement_vs_voting:>+6.1f}%")
    
    # Save results
    comparison_results = {
        'single_llm': single_accuracy,
        'simple_voting': voting_accuracy,
        'debate_system': debate_accuracy,
        'debate_problems_tested': len(results),
    }
    
    output_file = Path("data/results/baseline_comparison.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comparison_results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    print("\n" + "="*60)


if __name__ == "__main__":
    compare_all_systems()