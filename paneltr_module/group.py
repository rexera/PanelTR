import os
import random
import re
from pprint import pprint
import sys

# Add the parent directory to Python path to make agentic_I5 importable
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # Get the parent directory
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now import the local modules
try:
    from paneltr_module.single_agent import paneltr_single, generate_response
    from paneltr_module.config.paneltr_global_config import client, MODEL, REFLECTION_TURNS, TEMPERATURE
except ModuleNotFoundError as e:
    print(f"Error importing modules: {e}")
    print(f"sys.path: {sys.path}")
    raise

from threading import Lock

lock = Lock()

# Define personas for each role (scientist agents)
personas = {
    "Albert Einstein": "You are Albert Einstein, a theoretical physicist. Your responses should explore alternative interpretations and conceptual frameworks. Only speak on your behalf.",
    "Isaac Newton": "You are Isaac Newton, a mathematician and physicist. Your responses should verify numerical relationships and logical consistency. Only speak on your behalf.",
    "Marie Curie": "You are Marie Curie, a physicist and chemist. Your responses should validate with experimental evidence and practical tests. Only speak on your behalf.",
    "Alan Turing": "You are Alan Turing, a mathematician and computer scientist. Your responses should analyze problem structure and optimize solution efficiency. Only speak on your behalf.",
    "Nikola Tesla": "You are Nikola Tesla, an inventor and electrical engineer. Your responses should synthesize diverse perspectives into coherent solutions. Only speak on your behalf.",
}

def round_1(role, system_prompt, input_query):
    persona_prompt = (
        f"There are 5 scientist agents to solve a tabular reasoning task: "
        f"Albert Einstein, Isaac Newton, Marie Curie, Alan Turing, and Nikola Tesla. "
        f"{personas[role]}\n{system_prompt}"
    )
    final_output, _ = paneltr_single(persona_prompt, input_query)
    return final_output

def round_2(role, system_prompt, input_query, chat_history):
    persona_prompt = f"{personas[role]}\n{system_prompt}"
    messages = [
        {
            "role": "system",
            "content": (
                "There are 5 scientist agents to solve a tabular reasoning task: "
                "Albert Einstein, Isaac Newton, Marie Curie, Alan Turing, and Nikola Tesla. \n"
                f"Task Description: {persona_prompt}\n Following is your specific instance for the task:\n{input_query}"
            ),
        },
    ]
    for _ in chat_history:
        messages.append(_)
    messages.append({'content': "Now considering all of your previous initiatives, please: 1) give out your own step-by-step solution while responding to fellows' initiatives; 2) give out your final answer. Keep in a scientist's confronting manner and make your final answer polished. Notice that you are not required to always reach a consensus. Use structured free form with a fixed format: \n Final Answer:\n \n at the end of your response, with no other content attached.", 'role': 'system'})
    final_output = generate_response(messages)
    return final_output

def extract_final_answer(output):
    """Extract final answer from a single scientist agent's response"""
    # First try to find the last occurrence of "final answer:"
    pattern = r"final answer:[\s\n]*((?:.*\n?)*?)(?:\n\s*$|$)"
    match = re.search(pattern, output, re.IGNORECASE | re.MULTILINE)
    
    if match:
        # Clean up the extracted answer
        answer = match.group(1).strip()
        # Remove any additional "final answer:" that might be in the extracted text
        answer = re.sub(r'final answer:', '', answer, flags=re.IGNORECASE).strip()
        return answer
    return None

def check_consensus(answers):
    """Check if all agents agree on the same answer"""
    if not answers:
        return False
    return len(set(answers)) == 1

def paneltr_integrated(system_prompt, input_query, silent=True):
    roles = [
        "Albert Einstein",
        "Isaac Newton",
        "Marie Curie",
        "Alan Turing",
        "Nikola Tesla",
    ]
    chat_history = []

    # Phase 1: Individual Initiatives
    if not silent:
        print("\n" + "="*50)
        print("INDIVIDUAL INITIATIVES")
        print("="*50 + "\n")
    
    initial_answers = {}
    for role in roles:
        output = round_1(role, system_prompt, input_query)
        print(f"{role} finished individual initiative.")
        chat_history.append({'content': f"[{role}]: \n{output}", 'role': 'user'})
        initial_answers[role] = extract_final_answer(output)
        if not silent:
            print(f"\n\n[{role}]: \n{output}\n\n")

    # Phase 2: First Conference (必定进行的第一轮讨论)
    if not silent:
        print("\n" + "="*50)
        print("CONFERENCE - Round 1")
        print("="*50 + "\n")
    else:
        print("---First discussion round---")

    # First round of discussion
    random.shuffle(roles)
    first_round_answers = []
    for role in roles:
        output = round_2(role, system_prompt, input_query, chat_history)
        print(f"{role} spoke in the first discussion round.")
        chat_history.append({'content': f"[{role}]: \n{output}", 'role': 'user'})
        first_round_answers.append(extract_final_answer(output))
        if not silent:
            print(f"\n\n[{role}]: \n{output}\n\n")

    # Check consensus after first round
    if check_consensus(first_round_answers):
        if not silent:
            print("\nConsensus reached after first discussion!")
        return f"Final Answer: \n{first_round_answers[0]}", chat_history

    # Phase 3: Additional Reflection Rounds if needed
    current_round = 2  # Starting from 2 as we already had round 1
    final_answers = first_round_answers
    
    while current_round <= REFLECTION_TURNS + 1:  # +1 because we started from 2
        if not silent:
            print("\n" + "="*50)
            print(f"RE-DISCUSSION Round {current_round-1}")
            print("="*50 + "\n")
        else:
            print(f"---discussion round {current_round}---")
        
        # Add disagreement message
        disagreement_msg = {
            'content': "There are still disagreements among the scientist agents. Please discuss further to reach a consensus.",
            'role': 'system'
        }
        chat_history.append(disagreement_msg)
        if not silent:
            print("\n\nStarting another round of discussion due to disagreement...\n\n")

        # Next round of discussion
        random.shuffle(roles)
        round_answers = []
        for role in roles:
            output = round_2(role, system_prompt, input_query, chat_history)
            print(f"{role} spoke in discussion round {current_round}.")
            chat_history.append({'content': f"[{role}]: \n{output}", 'role': 'user'})
            round_answers.append(extract_final_answer(output))
            if not silent:
                print(f"\n\n[{role}]: \n{output}\n\n")
        
        final_answers = round_answers
        if check_consensus(final_answers):
            if not silent:
                print(f"\nConsensus reached in round {current_round}!")
            return f"Final Answer: \n{final_answers[0]}", chat_history
        
        current_round += 1

    # If we get here, it means no consensus was reached after all rounds
    def determine_final_answer(answers):
        answer_counts = {}
        for answer in answers:
            if answer and answer.strip():
                if answer in answer_counts:
                    answer_counts[answer] += 1
                else:
                    answer_counts[answer] = 1

        if not answer_counts:
            return "No conclusive answer reached"

        max_count = max(answer_counts.values())
        final_candidates = [answer for answer, count in answer_counts.items() if count == max_count]

        if len(final_candidates) == 1:
            return final_candidates[0]
        else:
            return random.choice(final_candidates)

    # Use majority vote for final decision
    final_answer = determine_final_answer(final_answers)
    if not silent:
        print(f"\nNo consensus reached after {current_round-1} rounds. Using majority vote.")

    return f"Final Answer: \n{final_answer}", chat_history

if __name__ == "__main__":
    # Add this to ensure the script can be run from any directory
    if not os.getcwd() in sys.path:
        sys.path.append(os.getcwd())
    
    system_prompt = (
        "The table includes quarterly financial data for various product lines in the fiscal year. Analyze it and answer the following question."
        "Response Format\n"
        "Final Answer:\n"
        "(your final answer)")

    input_query = """
        Blank filling.

        Q1: Based on the financial data provided in the table: What is the average profit margin for Product Line A across all quarters where its revenue exceeded $500,000?
        Q2: Then, compare this average with Product Line B's profit margin over the same quarters and determine: Which line had a higher average profit margin?
        Q3: 使用最小二乘法做回归分析. Predict the Q1 profit of the coming year for both product lines based on the trend observed in the table.

        # | Quarter | Product Line | Revenue  | Cost     | Profit   |
        # |---------|--------------|----------|----------|----------|
        # | Q1      | A            | 520,000  | 390,000  | 130,000  |
        # | Q2      | A            | 480,000  | 350,000  | 130,000  |
        # | Q3      | A            | 510,000  | 370,000  | 140,000  |
        # | Q4      | A            | 600,000  | 450,000  | 150,000  |
        # | Q1      | B            | 550,000  | 410,000  | 140,000  |
        # | Q2      | B            | 600,000  | 460,000  | 140,000  |
        # | Q3      | B            | 490,000  | 370,000  | 120,000  |
        # | Q4      | B            | 620,000  | 460,000  | 160,000  |

        Format: 
        Q1:____%
        Q2:Line____
        Q3: A:____ B:____
        """

    final_answer, chat_history = paneltr_single(system_prompt, input_query, silent=False)
    print(final_answer)