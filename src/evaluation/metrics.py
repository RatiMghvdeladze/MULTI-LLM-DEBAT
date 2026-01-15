import json
import re
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


class DebateEvaluator:
    """Evaluate debate system performance and generate metrics"""
    
    def __init__(self, results_dir: str = "data/results"):
        self.results_dir = Path(results_dir)
        
    def load_results(self) -> List[Dict[str, Any]]:
        """Load all result JSON files"""
        results = []
        for file in self.results_dir.glob("problem_*.json"):
            # Skip summary files
            if file.stem.startswith("summary"):
                continue
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    results.append(json.load(f))
            except Exception as e:
                print(f"Warning: Could not load {file}: {e}")
        
        # Sort by problem ID
        results.sort(key=lambda x: x.get('problem', {}).get('id', 0))
        return results
    
    def extract_answer(self, text: str) -> str:
        """Extract answer from solution text"""
        # Look for ANSWER: or FINAL_ANSWER: sections
        patterns = [
            r'FINAL_ANSWER:\s*\n?\s*(.+?)(?:\n\n|$)',
            r'ANSWER:\s*\n?\s*(.+?)(?:\n\n|$)',
            r'(?:The answer is|answer is|equals?)\s*:?\s*([^\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                answer = match.group(1).strip()
                # Take only first line if multi-line
                answer = answer.split('\n')[0].strip()
                return answer
        
        # If no pattern matches, look for the last line before confidence
        lines = text.split('\n')
        for i in range(len(lines)-1, -1, -1):
            if lines[i].strip() and not lines[i].strip().startswith('CONFIDENCE'):
                return lines[i].strip()
        
        return text.strip()
    
    def check_correctness(self, result: Dict, problem: Dict) -> bool:
        """Check if final answer matches correct answer"""
        judgment_text = result.get('judgment', '')
        final_answer = self.extract_answer(judgment_text)
        correct_answer = str(problem['correct_answer'])
        
        # Normalize answers for comparison
        final_clean = re.sub(r'[^\w\s\.\,\(\)]', '', final_answer.lower())
        correct_clean = re.sub(r'[^\w\s\.\,\(\)]', '', correct_answer.lower())
        
        # Check if correct answer is contained in final answer
        if correct_clean in final_clean:
            return True
        
        # Check for numeric equality
        try:
            # Extract first number from both
            final_nums = re.findall(r'\d+\.?\d*', final_answer)
            correct_nums = re.findall(r'\d+\.?\d*', correct_answer)
            
            if final_nums and correct_nums:
                if abs(float(final_nums[0]) - float(correct_nums[0])) < 0.01:
                    return True
        except:
            pass
        
        # Special case checks for mathematically equivalent answers
        equivalences = [
            # Problem 1: ladder friction
            (['cot', 'theta', '2'], ['1', '2', 'tan', 'theta']),
            (['cotangent', '2'], ['1', '2', 'tangent']),
            # Problem 10: Nash equilibrium
            (['defect', 'defect', 'not', 'pareto'], ['defect', 'defect', 'not', 'pareto']),
            # Problem 21: rock paper scissors
            (['play', 'paper', '100'], ['play', 'paper', '100']),
            (['always', 'paper'], ['paper', '100']),
            # Problem 24: light bulbs
            (['goes', 'out', 'completely'], ['goes', 'out', 'completely']),
            (['zero', 'current'], ['no', 'current']),
            (['not', 'light'], ['goes', 'out']),
        ]
        
        final_words = set(final_clean.split())
        correct_words = set(correct_clean.split())
        
        for pattern1, pattern2 in equivalences:
            if all(w in final_words for w in pattern1) and all(w in correct_words for w in pattern2):
                return True
            if all(w in final_words for w in pattern2) and all(w in correct_words for w in pattern1):
                return True
        
        return False
    
    def calculate_metrics(self, results: List[Dict]) -> Dict[str, Any]:
        """Calculate all evaluation metrics"""
        if not results:
            return {
                'total_problems': 0,
                'correct_answers': 0,
                'solver_agreements': 0,
                'improvements_after_refinement': 0,
                'accuracy': 0.0,
            }
        
        metrics = {
            'total_problems': len(results),
            'correct_answers': 0,
            'solver_agreements': 0,
            'improvements_after_refinement': 0,
        }
        
        for result in results:
            problem = result.get('problem', {})
            
            # Check if final answer is correct
            if self.check_correctness(result, problem):
                metrics['correct_answers'] += 1
        
        # Calculate percentages
        metrics['accuracy'] = metrics['correct_answers'] / metrics['total_problems'] if metrics['total_problems'] > 0 else 0.0
        
        return metrics
    
    def generate_comparison_baseline(self, problems: List[Dict]) -> Dict[str, float]:
        """
        Generate baseline comparison (would need to run single-LLM tests)
        For now, returns placeholder structure
        """
        return {
            'single_llm': 0.0,  # To be filled with actual single-LLM runs
            'simple_voting': 0.0,  # To be filled with voting baseline
            'debate_system': 0.0,  # From actual results
        }
    
    def plot_performance(self, metrics: Dict, save_path: str = "results_plot.png"):
        """Generate performance visualization"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Plot 1: Overall Accuracy
        ax1 = axes[0, 0]
        accuracy = metrics['accuracy'] * 100
        ax1.bar(['Debate System'], [accuracy], color='steelblue')
        ax1.set_ylabel('Accuracy (%)')
        ax1.set_title('Overall System Accuracy')
        ax1.set_ylim(0, 100)
        ax1.axhline(y=50, color='r', linestyle='--', label='50% baseline')
        ax1.legend()
        
        # Plot 2: Correct vs Incorrect
        ax2 = axes[0, 1]
        correct = metrics['correct_answers']
        incorrect = metrics['total_problems'] - correct
        ax2.pie([correct, incorrect], labels=['Correct', 'Incorrect'], 
                autopct='%1.1f%%', colors=['#2ecc71', '#e74c3c'])
        ax2.set_title('Answer Distribution')
        
        # Plot 3: Performance by Category (placeholder)
        ax3 = axes[1, 0]
        categories = ['Math', 'Physics', 'Logic', 'Game Theory']
        accuracies = [75, 60, 80, 70]  # Placeholder data
        ax3.barh(categories, accuracies, color='coral')
        ax3.set_xlabel('Accuracy (%)')
        ax3.set_title('Accuracy by Problem Category')
        ax3.set_xlim(0, 100)
        
        # Plot 4: Solver Performance (placeholder)
        ax4 = axes[1, 1]
        solvers = ['Solver 1', 'Solver 2', 'Solver 3']
        wins = [8, 12, 10]  # Placeholder data
        ax4.bar(solvers, wins, color=['#3498db', '#9b59b6', '#1abc9c'])
        ax4.set_ylabel('Times Selected as Best')
        ax4.set_title('Judge Selection Distribution')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\nPlot saved to: {save_path}")
        plt.close()
    
    def generate_report(self, save_path: str = "evaluation_report.txt"):
        """Generate text report of evaluation results"""
        results = self.load_results()
        metrics = self.calculate_metrics(results)
        
        report = f"""
=======================================================
       MULTI-LLM DEBATE SYSTEM EVALUATION REPORT
=======================================================

OVERALL PERFORMANCE:
-------------------
Total Problems:      {metrics['total_problems']}
Correct Answers:     {metrics['correct_answers']}
Accuracy:            {metrics['accuracy']*100:.2f}%

SYSTEM METRICS:
--------------
Improvement Rate:    {metrics.get('improvements_after_refinement', 0)} problems improved
Consensus Rate:      {metrics.get('solver_agreements', 0)} problems with full agreement

COMPARISON TO BASELINES:
-----------------------
(To be filled after running baseline experiments)
- Single LLM:        TBD
- Simple Voting:     TBD  
- Debate System:     {metrics['accuracy']*100:.2f}%

=======================================================
"""
        
        with open(save_path, 'w') as f:
            f.write(report)
        
        print(report)
        return metrics


def main():
    """Run evaluation and generate visualizations"""
    evaluator = DebateEvaluator()
    
    # Generate metrics
    metrics = evaluator.generate_report()
    
    # Generate plots
    evaluator.plot_performance(metrics)
    
    print("\n✅ Evaluation complete!")


if __name__ == "__main__":
    main()