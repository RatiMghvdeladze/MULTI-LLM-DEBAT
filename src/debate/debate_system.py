import json
from typing import Dict, List, Any
from src.models.gemini_wrapper import GeminiWrapper
from config.settings import SOLVER_CONFIGS, JUDGE_CONFIG


class DebateSystem:
    """Orchestrates the multi-LLM debate process"""
    
    def __init__(self):
        self.model = GeminiWrapper()
        
    def stage0_role_assignment(self, problem: Dict[str, Any]) -> Dict[str, str]:
        """
        Stage 0: Ask each LLM which role they prefer for this problem
        Returns role assignments
        """
        print("\n=== STAGE 0: Role Assignment ===")
        
        # For simplicity, use predefined roles
        # In full implementation, could ask models to self-assess
        assignments = {
            "Solver_1": SOLVER_CONFIGS[0],
            "Solver_2": SOLVER_CONFIGS[1],
            "Solver_3": SOLVER_CONFIGS[2],
            "Judge": JUDGE_CONFIG
        }
        
        print("Role assignments:")
        for role, config in assignments.items():
            print(f"  {role}: {config.get('role', 'Judge')}")
            
        return assignments
    
    def stage1_independent_solutions(
        self, 
        problem: Dict[str, Any],
        assignments: Dict[str, Dict]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Stage 1: Generate independent solutions from each solver
        """
        print("\n=== STAGE 1: Independent Solutions ===")
        solutions = {}
        
        prompt_template = """Problem: {question}

Provide a complete solution with step-by-step reasoning. Structure your response as:

REASONING:
[Your detailed step-by-step reasoning]

ANSWER:
[Your final answer]

CONFIDENCE:
[Your confidence level from 0 to 1]
"""
        
        for solver_id in ["Solver_1", "Solver_2", "Solver_3"]:
            print(f"\nGenerating solution from {solver_id}...")
            config = assignments[solver_id]
            
            prompt = prompt_template.format(question=problem["question"])
            response = self.model.generate_with_config(prompt, config)
            
            solutions[solver_id] = {
                "raw_response": response,
                "config": config
            }
            
        return solutions
    
    def stage2_peer_review(
        self,
        problem: Dict[str, Any],
        solutions: Dict[str, Dict],
        assignments: Dict[str, Dict]
    ) -> Dict[str, List[Dict]]:
        """
        Stage 2: Each solver reviews the other two solutions
        """
        print("\n=== STAGE 2: Peer Review ===")
        reviews = {solver: [] for solver in ["Solver_1", "Solver_2", "Solver_3"]}
        
        review_template = """Problem: {question}

Solution to review from {reviewer_id}:
{solution}

As {your_role}, critically evaluate this solution. Provide:

STRENGTHS:
- [List strengths]

WEAKNESSES:
- [List weaknesses]

ERRORS:
- [Identify any logical errors, calculation mistakes, or unjustified assumptions]

SUGGESTED_CHANGES:
- [Specific suggestions for improvement]

OVERALL_ASSESSMENT:
[promising_but_flawed / sound_solution / fundamentally_flawed]
"""
        
        solver_ids = ["Solver_1", "Solver_2", "Solver_3"]
        
        for reviewer in solver_ids:
            reviewer_config = assignments[reviewer]
            
            for target in solver_ids:
                if target != reviewer:
                    print(f"\n{reviewer} reviewing {target}...")
                    
                    prompt = review_template.format(
                        question=problem["question"],
                        reviewer_id=target,
                        solution=solutions[target]["raw_response"],
                        your_role=reviewer_config["role"]
                    )
                    
                    review = self.model.generate_with_config(prompt, reviewer_config)
                    
                    reviews[target].append({
                        "from": reviewer,
                        "review": review
                    })
        
        return reviews
    
    def stage3_refinement(
        self,
        problem: Dict[str, Any],
        solutions: Dict[str, Dict],
        reviews: Dict[str, List[Dict]],
        assignments: Dict[str, Dict]
    ) -> Dict[str, Dict]:
        """
        Stage 3: Each solver refines their solution based on peer feedback
        """
        print("\n=== STAGE 3: Refinement ===")
        refined_solutions = {}
        
        refinement_template = """Problem: {question}

Your original solution:
{original_solution}

Peer reviews you received:

Review 1 (from {reviewer1}):
{review1}

Review 2 (from {reviewer2}):
{review2}

Address each critique and produce your refined solution. Structure as:

RESPONSE_TO_CRITIQUES:
- [For each critique, explain whether you accept it and what changes you made]

REFINED_REASONING:
[Your improved step-by-step reasoning]

REFINED_ANSWER:
[Your final answer]

CONFIDENCE:
[Your confidence level from 0 to 1]
"""
        
        for solver_id in ["Solver_1", "Solver_2", "Solver_3"]:
            print(f"\n{solver_id} refining solution...")
            config = assignments[solver_id]
            solver_reviews = reviews[solver_id]
            
            prompt = refinement_template.format(
                question=problem["question"],
                original_solution=solutions[solver_id]["raw_response"],
                reviewer1=solver_reviews[0]["from"],
                review1=solver_reviews[0]["review"],
                reviewer2=solver_reviews[1]["from"],
                review2=solver_reviews[1]["review"]
            )
            
            refined = self.model.generate_with_config(prompt, config)
            
            refined_solutions[solver_id] = {
                "original": solutions[solver_id]["raw_response"],
                "refined": refined,
                "reviews_received": solver_reviews
            }
        
        return refined_solutions
    
    def stage4_final_judgment(
        self,
        problem: Dict[str, Any],
        solutions: Dict[str, Dict],
        reviews: Dict[str, List[Dict]],
        refined_solutions: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """
        Stage 4: Judge evaluates all solutions and picks the best
        """
        print("\n=== STAGE 4: Final Judgment ===")
        
        judgment_template = """Problem: {question}

You are judging three solutions to this problem.

SOLVER 1 REFINED SOLUTION:
{solver1_refined}

SOLVER 2 REFINED SOLUTION:
{solver2_refined}

SOLVER 3 REFINED SOLUTION:
{solver3_refined}

Evaluate all solutions and determine which is best. Provide:

ANALYSIS:
[Compare the solutions, identify strengths and weaknesses of each]

WINNER:
[Solver_1, Solver_2, or Solver_3]

REASONING:
[Explain why this solution is best]

CONFIDENCE:
[Your confidence in this judgment from 0 to 1]

FINAL_ANSWER:
[The answer from the winning solution]
"""
        
        prompt = judgment_template.format(
            question=problem["question"],
            solver1_refined=refined_solutions["Solver_1"]["refined"],
            solver2_refined=refined_solutions["Solver_2"]["refined"],
            solver3_refined=refined_solutions["Solver_3"]["refined"]
        )
        
        judgment = self.model.generate_with_config(prompt, JUDGE_CONFIG)
        
        return {
            "judgment": judgment,
            "problem": problem,
            "all_solutions": refined_solutions
        }
    
    def run_debate(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run complete debate process on a single problem
        """
        print(f"\n{'='*60}")
        print(f"PROBLEM {problem['id']}: {problem['question'][:80]}...")
        print(f"{'='*60}")
        
        # Stage 0: Role Assignment
        assignments = self.stage0_role_assignment(problem)
        
        # Stage 1: Independent Solutions
        solutions = self.stage1_independent_solutions(problem, assignments)
        
        # Stage 2: Peer Review
        reviews = self.stage2_peer_review(problem, solutions, assignments)
        
        # Stage 3: Refinement
        refined_solutions = self.stage3_refinement(problem, solutions, reviews, assignments)
        
        # Stage 4: Final Judgment
        result = self.stage4_final_judgment(problem, solutions, reviews, refined_solutions)
        
        return result