from paneltr_module.config.paneltr_global_config import client, MODEL, REFLECTION_TURNS, TEMPERATURE

identify = '''Assess task difficulty and evaluate the potential challenges in solving it, providing key points to 
consider based on specifically difficult factors. Avoid directly solving the problem or adhering to the final task 
response format.

When assessing difficulty, ensure the following:
- Take a deep breath and figure out what your task is. Do not go beyond the task.
- Be humble and honest about the complexity, as the task might be challenging.
- Clearly highlight critical factors or considerations that could impact the resolution of the task.
- Avoid general terms and provide specific details that are relevant to the instance at hand.
'''

format_1 = '''
Format:

IDENTIFICATION
Task for this instance: (One line summary)
Overall Complexity: Easy / Medium / Hard

Key Notices:  
1. ...  
2. ...  
...

Guidance:
Step 1: ...
Step 2: ...
...
'''

improvise = '''
Plan a set of reasonable steps to solve the problem based on the task's difficulty and key considerations, and arrive at the **final answer**. When presenting the final answer, ensure it adheres to the required response format.

Guidelines for the process:
- Take a deep breath and figure out what your task is. Do not go beyond the task.
- Focus on improving the accuracy of the final answer; the thought process is a means to that end.
- Avoid excessive focus on minor, unimportant details and prioritize elements that directly enhance the accuracy of the final answer.
- Base reasoning and conclusions on known information, avoiding speculation on unknowns.

Ensure the final answer is presented clearly, without further explanation or elaboration.
'''

format_2 = '''
Format:

IMRPOVISATION
Let's come up with a specific solution for this very instance!
Task for this instance: (in one line)
I should notice: (keys from previous identification, one line)

Steps:
1.
2.
3.
...

Final Answer:
...
(your final answer formatted according to task description)
'''

inspect = '''
Carefully review and analyze the current problem-solving process and final answer, identifying potential issues in the reasoning or approach.

Guidelines for the review:
- Take a deep breath and figure out what your task is. Do not go beyond the task.
- Focus on improving the accuracy of the final answer; refining the reasoning process is a means to this goal.
- Avoid overanalyzing minor or irrelevant details, directing attention toward elements that significantly impact the final answer's accuracy.
- Ground observations and critiques in the known information, refraining from speculation about unknown factors.
- Do not critique for the sake of critique; if the solution is sound, acknowledge it.

After your analysis, decide whether to:
1. FINALIZE - if the solution is sound and ready for final output
2. REFINE - if the solution needs further improvement

End your response with either "Decision: FINALIZE" or "Decision: REFINE"
'''

format_3 = '''
Format:

INSPECTION
Analysis:

On reasoning chain:
1.
2.
3.
...

On final answer:
1.
2.
3.
...

Decision: [FINALIZE/REFINE]
'''

re_improvise = '''Review and refine the problem-solving steps and the final answer with the aim of enhancing the accuracy of the final result. Trust your intuition and avoid unnecessary doubt.

Guidelines for the review:
- Take a deep breath and figure out what your task is. Do not go beyond the task.
- Focus on ensuring the final answer is as accurate and reliable as possible.
- Correct possible mistakes in task description, reasoning chain, or final answer (format and content).
- Avoid overthinking or second-guessing unnecessarily; make calm decisions based on the given information.
- Do not critique for the sake of critique; if the solution is sound, acknowledge it.
- Offer a refined solution.
'''

format_4 = '''
Format:

RE-IMRPOVISATION
Let's refine the specific solution for this very instance!
Task for this instance: (in one line)
I should notice: (keys from all previous steps, in one line)

Steps:
1.
2.
3.
...

Final Answer:
...
(your final answer formatted according to task description)
'''

final = '''
Carefully review and analyze the current problem-solving process and final answer; make one last improvement to address potential issues and arrive at the **final answer**.

Guidelines for this review and improvement:
- Take a deep breath and figure out what your task is. Do not go beyond the task.
- Ensure your response concords with the task requirements and adheres to the specified format.
- Focus solely on improving the accuracy and reliability of the final answer.
- Treat the refinement of the reasoning process as a means to achieve higher accuracy in the final result.
- Avoid over-focusing on trivial details, directing effort toward addressing critical issues that impact the final answer’s correctness.

Conclude with the final answer clearly and concisely, ensuring it is presented without additional elaboration or explanation.
'''

format_5 = '''
Format:

FINAL SOLUTION

1.
2.
3.
...

Final Answer:
(your final answer formatted according to task description)
'''

IDENTIFY = f"Now please IDENTIFY.\n{identify}\n{format_1}"
IMPROVISE = f"Now please IMPROVISE.\n{improvise}\n{format_2}"
INSPECT = f"Now please INSPECT.\n{inspect}\n{format_3}"
RE_IDENTIFY = f"Now please RE-IDENTIFY.\n{identify}\n{format_1}"
RE_IMPROVISE = f"Now please RE-IMPROVISE.\n{re_improvise}\n{format_4}"
RE_INSPECT = f"Now please RE-INSPECT.\n{inspect}\n{format_3}"
FINALIZE = f"Now please FINALIZE.\n{final}\n{format_5}"


def generate_response(messages):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE
    )
    response_content = response.choices[0].message.content
    '''print("-"*80)
    print(response_content)
    print("-" * 80)'''
    return response_content

internal = []

def paneltr_single(system_prompt, input_query):
    messages = [
        {"role": "system",
         "content": f"Task Description: {system_prompt}\n Following is your specific instance for the task:\n{input_query}"},
    ]

    def append_message(content):
        messages.append({"role": 'user', "content": f'{content}'})

    def process_iteration(is_first_iteration=True):
        # Choose prompts based on iteration
        identify_prompt = IDENTIFY if is_first_iteration else RE_IDENTIFY
        improvise_prompt = IMPROVISE if is_first_iteration else RE_IMPROVISE
        
        # Identification and improvisation
        for prompt in [identify_prompt, improvise_prompt]:
            append_message(prompt)
            response = generate_response(messages)
            messages.pop()
            internal.append(response)
            append_message(f"Previous Process: \n{response}")
        
        # Inspection and decision
        append_message(INSPECT)
        response = generate_response(messages)
        messages.pop()
        internal.append(response)
        
        # Check if model decides to finalize
        if response and "Decision: FINALIZE" in response:
            append_message(FINALIZE)
            final_response = generate_response(messages)
            internal.append(final_response)
            return True, final_response
        
        append_message(f"Previous Process: \n{response}")
        return False, None

    iterations = 0
    while iterations < REFLECTION_TURNS:
        is_final, final_response = process_iteration(is_first_iteration=(iterations == 0))
        if is_final:
            return final_response, internal
        iterations += 1
    
    # If max iterations reached without finalization, force finalize
    append_message(FINALIZE)
    final_response = generate_response(messages)
    internal.append(final_response)
    return final_response, internal


if __name__ == "__main__":
    system_prompt = (
        "The table includes quarterly financial data for various product lines in the fiscal year. Analyze it and answer the following question."
        "最后用固定格式回答：\n"
        "Final Answer:\n"
        "(your final answer)")

    input_query = """
    Blank filling.
    
    Q1: Based on the financial data provided in the table: What is the average profit margin for Product Line A across all quarters where its revenue exceeded $500,000?
    Q2: Then, compare this average with Product Line B's profit margin over the same quarters and determine: Which line had a higher average profit margin?

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
    """

    final_output, internal = paneltr_single(system_prompt, input_query)
    print("Final Output:", final_output)