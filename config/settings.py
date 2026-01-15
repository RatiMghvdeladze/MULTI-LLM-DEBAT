import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.0-flash-exp"

# Solver Configurations (different temperatures for diversity)
SOLVER_CONFIGS = [
    {
        "name": "Solver_1",
        "role": "Mathematical Rigor Specialist",
        "system_prompt": "You are a solver who prioritizes mathematical rigor and formal proofs. Break down problems systematically with clear logical steps.",
        "temperature": 0.7,
        "top_p": 0.9,
    },
    {
        "name": "Solver_2", 
        "role": "Intuitive Problem Solver",
        "system_prompt": "You are a solver who uses intuition and creative approaches. Look for patterns and elegant solutions.",
        "temperature": 0.8,
        "top_p": 0.95,
    },
    {
        "name": "Solver_3",
        "role": "Edge Case Hunter",
        "system_prompt": "You are a solver who focuses on edge cases and boundary conditions. Question assumptions and test limits.",
        "temperature": 0.6,
        "top_p": 0.85,
    },
]

# Judge Configuration
JUDGE_CONFIG = {
    "name": "Judge",
    "system_prompt": "You are an impartial judge evaluating solutions. Focus on correctness, completeness, and logical soundness.",
    "temperature": 0.3,
    "top_p": 0.8,
}

# Paths
DATA_DIR = "data"
PROBLEMS_FILE = os.path.join(DATA_DIR, "problems", "problems.json")
RESULTS_DIR = os.path.join(DATA_DIR, "results")

# Ensure directories exist
os.makedirs(os.path.join(DATA_DIR, "problems"), exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)