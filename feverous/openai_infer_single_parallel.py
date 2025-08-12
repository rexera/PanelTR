import os
from datetime import datetime
from pprint import pprint

import jsonlines
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Lock
from paneltr_module.single_agent import paneltr_single

prompt = '''
You are an expert in question answering.
You will be given a claim and relevant set of evidence.
Verdict the claim as "SUPPORTS", "REFUTES", or "NOT ENOUGH INFO" based on given evidence.

Guidance:
- For a claim to be marked as "SUPPORTS", every piece of information in the claim must be backed by evidence.
- To mark a claim as "REFUTES", you only need to find sufficient evidence that contradicts any part of the claim. Even if the rest of the claim might be accurate, refuting one section is enough.
- A claim is classified as "NOT ENOUGH INFO" if there is not enough information available in the provided evidence to verify or refute it. This typically happens when the relevant data is missing, incomplete, or ambiguous.

Your answer format should be:

Final Answer:
(choose from "SUPPORTS", "REFUTES", or "NOT ENOUGH INFO")

'''

lock = Lock()
#timestamp = datetime.now().strftime("%m%d_%H%M")


def gpt(input_sentence):
    answer, collaboration = paneltr_single(prompt, input_sentence)
    try:
        import re
        match = re.search(r"final answer:\s*(supports|refutes|not enough info)", answer, re.IGNORECASE)
        if match:
            final_inference = match.group(1).lower()
            print(final_inference)
            return final_inference
        else:
            return collaboration
    except Exception as e:
        print(f"Error extracting final answer: {e}")
        return "NONE"

def read_jsonl_file(file_path):
    if os.path.exists(file_path):
        data = []
        try:
            with jsonlines.open(file_path, 'r') as reader:
                for obj in reader:
                    data.append(obj)
        except Exception as e:
            print(f"Error reading data from {file_path}: {e}")
        return data
    return []

def write_jsonl_file(file_path, data, append=False):
    mode = 'a' if append else 'w'
    with jsonlines.open(file_path, mode=mode) as writer:
        for entry in data:
            writer.write(entry)

def save_batch_results(output_jsonl_path, results, batch_num):
    with lock:
        write_jsonl_file(output_jsonl_path, results, append=True)
        print(f"Saved batch {batch_num} to {output_jsonl_path}")

def process_item(item):
    try:
        claim = item['claim']
        evidence = item['evidence']
        input_sentence = f"Claim: {claim}\nEvidence: {evidence}"
        prediction = gpt(input_sentence)
        return {"index": item['index'], "prediction": prediction}
    except Exception as e:
        print(f"Error processing item with id {item['index']}: {e}")
        return None

def main(input_jsonl_path, output_jsonl_path, batch_size=10):
    input_data = read_jsonl_file(input_jsonl_path)
    existing_results = read_jsonl_file(output_jsonl_path)
    processed_indices = {item['index'] for item in existing_results}
    filtered_data = [item for item in input_data if item['index'] not in processed_indices]
    skipped_ids = [item['index'] for item in input_data if item['index'] in processed_indices]
    if skipped_ids:
        pprint(f"Skipping ids: {skipped_ids}")

    batch_num = 1
    with tqdm(total=len(filtered_data), desc="Processing") as pbar:
        for i in range(0, len(filtered_data), batch_size):
            batch = filtered_data[i:i + batch_size]
            with ProcessPoolExecutor(max_workers=batch_size) as executor:
                future_to_item = {executor.submit(process_item, item): item for item in batch}
                batch_results = []
                for future in as_completed(future_to_item):
                    result = future.result()
                    if result:
                        batch_results.append(result)
                    pbar.update(1)
                if batch_results:
                    sorted_results = sorted(batch_results, key=lambda x: x['index'])
                    save_batch_results(output_jsonl_path, sorted_results, batch_num)
                    batch_num += 1

if __name__ == "__main__":
    input_jsonl_path = '/./PanelTR/feverous/data_openai/feverous_dev_gpt_final_tweaked_w_index.jsonl'
    output_jsonl_path = f'/./PanelTR/feverous/output/single_ds_0109_11.jsonl'
    main(input_jsonl_path, output_jsonl_path, batch_size=10)