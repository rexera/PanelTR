import re
import json
from pprint import pprint
from tqdm import tqdm
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Lock
from paneltr_module.single_agent import paneltr_single

save_lock = Lock()
prompt = '''
Task Description:
Below is an instruction that describes a question answering task in the finance domain, paired with an input table and its relevant text that provide further context. The given question is relevant to the table and text. Generate an appropriate answer to the given question.

- `answer`: any `float`, `string` or a list with `float` or `string`. could be a sentence 'string'. when impossible to answer, leave blank ("")
- `scale`: `string`. ONLY choose from ['thousand', 'million', 'billion', 'percent'] when not applicable, leave blank ("")
For one question, give two responses in this following set format. (DO NOT forget the indicator, i.e. Final Answer and Scale)

For example,

Final Answer:
["answer1", "answer2", "answer3", ...]
Scale: "thousand"
'''

def gpt(input_sentence):
    answer, collaboration = paneltr_single(prompt, input_sentence)
    return answer, collaboration

def extract_answer_and_scale(gpt_output):
    try:
        # Initialize final_answer_list and scale
        final_answer_list = []
        scale = ""

        # Case 1: Both Final Answer and Scale are present
        list_match = re.search(r'Final Answer:\s*\[(.*?)\]\s*Scale:\s*"([^"]*)"', gpt_output, re.DOTALL)
        if list_match:
            final_answer = list_match.group(1).strip()
            final_answer_list = re.findall(r'\"(.*?)\"', final_answer)
            if not final_answer_list:  # If no matches found, check for numbers and nested lists
                final_answer_list = re.findall(r'[-+]?\d*\.\d+|\d+|\[.*?\]', final_answer)
            scale = list_match.group(2).strip()
        else:
            # Case 2: Only Final Answer is present
            list_match = re.search(r'Final Answer:\s*\[(.*?)\]', gpt_output, re.DOTALL)
            if list_match:
                final_answer = list_match.group(1).strip()
                final_answer_list = re.findall(r'\"(.*?)\"', final_answer)
                if not final_answer_list:  # If no matches found, check for numbers and nested lists
                    final_answer_list = re.findall(r'[-+]?\d*\.\d+|\d+|\[.*?\]', final_answer)
            else:
                # Case 3: No specific prompt, try to extract any potential answer
                fallback_match = re.findall(r'[-+]?\d*\.\d+|\d+|\[.*?\]', gpt_output)
                final_answer_list = fallback_match if fallback_match else ["NONE"]

        # Case 4: No content extracted, return ["NONE"]
        if not final_answer_list or final_answer_list == [""]:
            final_answer_list = ["NONE"]

        return final_answer_list, scale
    except Exception as e:
        print(f"Error extracting answer and scale: {e}")
        return ["NONE"], ""

def load_existing_results(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

def save_results(results, filename):
    with save_lock:
        existing_results = load_existing_results(filename)
        for uid, value in results.items():
            index = value[0]
            if index not in [v[0] for v in existing_results.values()]:
                existing_results[uid] = value
        sorted_results = dict(sorted(existing_results.items(), key=lambda item: item[1][0]))
        with open(filename, 'w') as outfile:
            json.dump(sorted_results, outfile, indent=4)
        print(f"Results saved to {filename}")

def process_item(item):
    print(f"Processing item with id {item['uid']}")
    try:
        question_uid = item['uid']
        question_text = item['question']
        question_index = item['index']
        table_data = item['table']['table']
        paragraphs = [p['text'] for p in item['paragraphs']]
        gpt_input = f"Table:\n{table_data}\nParagraphs:\n{paragraphs}\nQuestion:\n{question_text}\n"
        gpt_output, collaboration = gpt(gpt_input)
        final_answer, scale = extract_answer_and_scale(gpt_output)
        print(f"Final Answer: {final_answer}, Scale: {scale}")
        if final_answer == ["NONE"]:
            return question_uid, [question_index, final_answer, scale, collaboration]
        else:
            return question_uid, [question_index, final_answer, scale, gpt_output]
    except Exception as e:
        print(f"Error processing question {item['uid']}: {e}")
        return None

def main():
    input_file_path = '/./PanelTR/tat-qa/dataset_raw/tatqa_dataset_dev_w_index.json'
    output_file_path = '/./PanelTR/tat-qa/output/single_ds_dev_0106_18.json'
    with open(input_file_path, 'r') as file:
        data = json.load(file)

    existing_results = load_existing_results(output_file_path)
    processed_uids = set(existing_results.keys())
    processed_indices = {value[0] for value in existing_results.values()}
    all_questions = [
        {'uid': question['uid'], 'question': question['question'], 'index': question['index'], 'table': item['table'], 'paragraphs': item['paragraphs']}
        for item in data if isinstance(item, dict) and 'questions' in item
        for question in item['questions']
    ]

    # Filter out questions with uids already processed
    filtered_questions = [item for item in all_questions if item['uid'] not in processed_uids]
    skipped_uids = [item['uid'] for item in all_questions if item['uid'] in processed_uids]
    if skipped_uids:
        pprint(f"Skipping uids: {skipped_uids}")

    batch_size = 10

    with tqdm(total=len(filtered_questions), desc="Processing all questions") as pbar:
        for i in range(0, len(filtered_questions), batch_size):
            batch = filtered_questions[i:i + batch_size]
            with ProcessPoolExecutor(max_workers=batch_size) as executor:
                future_to_item = {executor.submit(process_item, item): item for item in batch}
                batch_results = []
                for future in as_completed(future_to_item):
                    result = future.result()
                    if result:
                        batch_results.append(result)
                    pbar.update(1)
                if batch_results:
                    gpt_results = {uid: data for uid, data in batch_results}
                    save_results(gpt_results, output_file_path)

if __name__ == "__main__":
    main()