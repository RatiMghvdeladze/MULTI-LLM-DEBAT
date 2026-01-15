"""Check judgment parsing in results"""
import json
from pathlib import Path

def check_judgments():
    results_dir = Path("data/results")
    
    print("="*60)
    print("CHECKING JUDGMENT PARSING")
    print("="*60)
    
    winners_found = []
    problems_checked = 0
    
    for file in sorted(results_dir.glob("problem_*.json"))[:5]:  # Check first 5
        if file.stem.startswith("summary"):
            continue
            
        problems_checked += 1
        
        with open(file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        problem_id = result.get('problem', {}).get('id', 'N/A')
        judgment = result.get('judgment', '')
        
        print(f"\n--- Problem {problem_id} ---")
        
        # Show WINNER line
        winner_found = False
        for line in judgment.split('\n'):
            if 'WINNER' in line.upper():
                print(f"Winner line: {line}")
                winner_found = True
                
                # Try to extract
                if ':' in line:
                    parts = line.split(':', 1)
                    winner_text = parts[1].strip()
                    winner_word = winner_text.split()[0] if winner_text.split() else "NONE"
                    print(f"Extracted: '{winner_word}'")
                    winners_found.append(winner_word)
                break
        
        if not winner_found:
            print("⚠️ No WINNER line found!")
            print("First 200 chars of judgment:")
            print(judgment[:200])
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Problems checked: {problems_checked}")
    print(f"Winners extracted: {len(winners_found)}")
    print(f"Winners found: {winners_found}")
    
    if winners_found:
        from collections import Counter
        counts = Counter(winners_found)
        print("\nWinner distribution:")
        for winner, count in counts.items():
            print(f"  {winner}: {count}")

if __name__ == "__main__":
    check_judgments()