"""
Generate all evaluation plots and reports
Run this from project root: python generate_plots.py
"""
import sys
from pathlib import Path
from src.evaluation.metrics import DebateEvaluator
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from collections import Counter

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

def main():
    print("="*60)
    print("GENERATING EVALUATION PLOTS")
    print("="*60)
    
    # Load results
    print("\n📂 Loading results...")
    evaluator = DebateEvaluator()
    results = evaluator.load_results()
    
    if len(results) == 0:
        print("❌ No results found! Run: python main.py --all")
        return
    
    print(f"✅ Loaded {len(results)} results")
    
    # Calculate metrics
    print("\n📊 Calculating metrics...")
    metrics = evaluator.calculate_metrics(results)
    
    print(f"   Total Problems: {metrics['total_problems']}")
    print(f"   Correct: {metrics['correct_answers']}")
    print(f"   Accuracy: {metrics['accuracy']*100:.2f}%")
    
    # Create results directory
    results_dir = Path("data/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Plot 1: Overall Performance
    print("\n🎨 Generating Plot 1: Overall Performance...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Accuracy bar
    axes[0].bar(['Debate System'], [metrics['accuracy']*100], color='steelblue', width=0.5)
    axes[0].set_ylabel('Accuracy (%)', fontsize=12)
    axes[0].set_title('Overall System Accuracy', fontsize=14, fontweight='bold')
    axes[0].set_ylim(0, 100)
    axes[0].axhline(y=50, color='r', linestyle='--', alpha=0.5, label='Random baseline')
    axes[0].legend()
    
    # Add percentage text
    for i, v in enumerate([metrics['accuracy']*100]):
        axes[0].text(i, v + 2, f'{v:.1f}%', ha='center', fontweight='bold', fontsize=14)
    
    # Success/Failure pie
    correct = metrics['correct_answers']
    incorrect = metrics['total_problems'] - correct
    
    axes[1].pie([correct, incorrect], 
                labels=[f'Correct ({correct})', f'Incorrect ({incorrect})'],
                autopct='%1.1f%%', 
                colors=['#2ecc71', '#e74c3c'],
                startangle=90,
                textprops={'fontsize': 12})
    axes[1].set_title('Answer Distribution', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plot1_path = results_dir / 'overall_performance.png'
    plt.savefig(plot1_path, dpi=300, bbox_inches='tight')
    print(f"   ✅ Saved: {plot1_path}")
    plt.close()
    
    # Plot 2: Category Performance
    print("\n🎨 Generating Plot 2: Category Performance...")
    problem_df = pd.DataFrame([
        {
            'id': r['problem']['id'],
            'category': r['problem']['category'],
            'correct': evaluator.check_correctness(r, r['problem'])
        }
        for r in results
    ])
    
    category_stats = problem_df.groupby('category')['correct'].agg(['sum', 'count', 'mean'])
    category_stats.columns = ['Correct', 'Total', 'Accuracy']
    category_stats['Accuracy'] = category_stats['Accuracy'] * 100
    
    plt.figure(figsize=(10, 6))
    colors = plt.cm.viridis(np.linspace(0, 0.8, len(category_stats)))
    
    bars = plt.barh(range(len(category_stats)), category_stats['Accuracy'], color=colors)
    plt.yticks(range(len(category_stats)), category_stats.index)
    plt.xlabel('Accuracy (%)', fontsize=12)
    plt.title('Accuracy by Problem Category', fontsize=14, fontweight='bold')
    plt.xlim(0, 100)
    
    # Add percentage labels
    for i, (idx, row) in enumerate(category_stats.iterrows()):
        plt.text(row['Accuracy'] + 2, i, f"{row['Accuracy']:.1f}% ({int(row['Correct'])}/{int(row['Total'])})",
                va='center', fontweight='bold')
    
    plt.tight_layout()
    plot2_path = results_dir / 'category_performance.png'
    plt.savefig(plot2_path, dpi=300, bbox_inches='tight')
    print(f"   ✅ Saved: {plot2_path}")
    plt.close()
    
    # Plot 3: Judge Decisions
    print("\n🎨 Generating Plot 3: Judge Decisions...")
    judge_decisions = []
    for r in results:
        judgment = r.get('judgment', '')
        
        # Try multiple parsing strategies
        winner = None
        
        # Strategy 1: Look for "WINNER: Solver_X" on same line
        for line in judgment.split('\n'):
            if 'WINNER:' in line and len(line.split(':')) > 1:
                winner_text = line.split(':', 1)[1].strip()
                if winner_text and 'Solver' in winner_text:
                    # Extract Solver_1, Solver_2, or Solver_3
                    words = winner_text.split()
                    for word in words:
                        if word.startswith('Solver'):
                            winner = word
                            break
                    if winner:
                        break
        
        # Strategy 2: Look for "WINNER:" then next non-empty line
        if not winner:
            lines = judgment.split('\n')
            for i, line in enumerate(lines):
                if 'WINNER:' in line:
                    # Check next few lines for Solver_X
                    for j in range(i+1, min(i+4, len(lines))):
                        next_line = lines[j].strip()
                        if next_line and 'Solver' in next_line:
                            words = next_line.split()
                            for word in words:
                                if word.startswith('Solver'):
                                    winner = word.rstrip('.,;:')  # Remove punctuation
                                    break
                            if winner:
                                break
                    if winner:
                        break
        
        # Strategy 3: Search anywhere in judgment for "Solver_X" near decision text
        if not winner:
            if 'best' in judgment.lower() or 'winner' in judgment.lower():
                for word in judgment.split():
                    if word.startswith('Solver'):
                        winner = word.rstrip('.,;:\'")')
                        break
        
        if winner:
            judge_decisions.append(winner)
    
    if judge_decisions:
        winner_counts = Counter(judge_decisions)
        
        plt.figure(figsize=(8, 6))
        solvers = list(winner_counts.keys())
        counts = list(winner_counts.values())
        colors_map = {'Solver_1': '#3498db', 'Solver_2': '#9b59b6', 'Solver_3': '#1abc9c'}
        bar_colors = [colors_map.get(s, '#95a5a6') for s in solvers]
        
        bars = plt.bar(solvers, counts, color=bar_colors, width=0.6)
        plt.ylabel('Number of Times Selected', fontsize=12)
        plt.title('Judge Selection Distribution', fontsize=14, fontweight='bold')
        plt.xlabel('Solver', fontsize=12)
        
        # Add count labels
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        plt.tight_layout()
        plot3_path = results_dir / 'judge_decisions.png'
        plt.savefig(plot3_path, dpi=300, bbox_inches='tight')
        print(f"   ✅ Saved: {plot3_path}")
        plt.close()
        
        print("\n🏆 Judge Preferences:")
        for solver, count in winner_counts.most_common():
            pct = count / len(judge_decisions) * 100
            print(f"   {solver}: {count} times ({pct:.1f}%)")
    
    # Plot 4: Problem Difficulty
    print("\n🎨 Generating Plot 4: Success by Problem ID...")
    plt.figure(figsize=(12, 6))
    
    problem_df_sorted = problem_df.sort_values('id')
    colors_success = ['#2ecc71' if c else '#e74c3c' for c in problem_df_sorted['correct']]
    
    plt.bar(problem_df_sorted['id'], [1]*len(problem_df_sorted), color=colors_success, width=0.8)
    plt.xlabel('Problem ID', fontsize=12)
    plt.ylabel('Result', fontsize=12)
    plt.title('Success/Failure by Problem', fontsize=14, fontweight='bold')
    plt.yticks([0, 1], ['', ''])
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2ecc71', label='Correct'),
        Patch(facecolor='#e74c3c', label='Incorrect')
    ]
    plt.legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()
    plot4_path = results_dir / 'problem_results.png'
    plt.savefig(plot4_path, dpi=300, bbox_inches='tight')
    print(f"   ✅ Saved: {plot4_path}")
    plt.close()
    
    # Generate text report
    print("\n📝 Generating evaluation report...")
    report_path = evaluator.generate_report(str(results_dir / 'evaluation_report.txt'))
    
    # Summary
    print("\n" + "="*60)
    print("✅ ALL PLOTS GENERATED SUCCESSFULLY!")
    print("="*60)
    print(f"\n📁 Output Location: {results_dir}/")
    print("\nGenerated files:")
    print("  1. overall_performance.png")
    print("  2. category_performance.png")
    print("  3. judge_decisions.png")
    print("  4. problem_results.png")
    print("  5. evaluation_report.txt")
    print("\n📊 Quick Summary:")
    print(f"  Total Problems: {metrics['total_problems']}")
    print(f"  Accuracy: {metrics['accuracy']*100:.1f}%")
    print(f"  Correct: {metrics['correct_answers']}")
    print(f"  Incorrect: {metrics['total_problems'] - metrics['correct_answers']}")
    print("\n" + "="*60)

if __name__ == "__main__":
    main()