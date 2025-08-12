import os
from datetime import datetime
from pprint import pprint

import jsonlines
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Lock
from paneltr_module.single_agent import paneltr_single

save_lock = Lock()
#timestamp = datetime.now().strftime("%m%d_%H%M")

system_prompt = '''
Based on the given table and relevant texts, determine whether a statement is **entailed**, **refuted**, or **unknown**.

"entailed": you can directly or indirectly extract info and decide on its being entailed.
"refuted": there is information about the statement that offers you reasons to refute it.
"unknown": when in some cases, the statement cannot be determined from the table or there is insufficient information to make a determination.

请注意，最后的答案是自动提取的，所以请不要在中间过程中使用entailed, refuted, or unknown这三个词。

Final Response Format:(make sure you write out the indicator "Final Answer:")

Final Answer:
(choose from entailed/refuted/unknown)
'''

prompt_template = '''
Table:
{table}

Notes:
{notes}

Statement:
{statement}
'''

def gpt(table, notes, statement):
    prompt = prompt_template.format(
        table=table,
        notes=notes,
        statement=statement
    )
    answer, collaboration = paneltr_single(system_prompt, prompt)
    try:
        final_answer_index = answer.lower().find("final answer:")
        if final_answer_index != -1:
            final_answer = answer[final_answer_index + len("final answer:"):].strip()
            final_inference = final_answer.split()[0].replace('*', '').lower()
            if final_inference in ['entailed', 'refuted', 'unknown']:
                print(final_inference)
                return final_inference
            else:
                print("UNABLE TO EXTRACT")
                return collaboration
        else:
            return collaboration
    except Exception as e:
        print(f"Error extracting final answer: {e}")
        return "UNKNOWN"

def read_jsonl_file(file_path):
    if os.path.exists(file_path):
        data = []
        with jsonlines.open(file_path, 'r') as reader:
            for obj in reader:
                data.append(obj)
        return data
    return []

def save_results(results, output_jsonl_path):
    with save_lock:
        with jsonlines.open(output_jsonl_path, mode='a') as writer:
            for result in results:
                writer.write(result)
        print(f"Results saved to {output_jsonl_path}")

def process_item(item):
    result = {}
    print(f"Processing item with id {item['global_id']}")
    try:
        xml_id = item['xml_id']
        table_id = item.get('table_id', '')
        table = item['rows']
        table_rows = "\n".join([", ".join(row) for row in table])
        table_content = f"Caption: {item['caption']}\nRows:\n{table_rows}"
        notes = f"Legend: {item.get('legend', '')}\nFootnote: {item.get('footnote', '')}"

        statement_obj = item
        statement_id = statement_obj['id']
        statement = statement_obj['text']
        global_id = statement_obj['global_id']
        prediction_type = gpt(table_content, notes, statement)
        print(prediction_type)
        result = {
            "global_id": global_id,
            "xml_id": xml_id,
            "table_id": table_id,
            "statement_id": statement_id,
            "type": prediction_type
        }
    except Exception as e:
        print(f"Error processing item with id {global_id}: {e}")
    return result

def main(input_jsonl_path, output_jsonl_path, batch_size=10):
    input_data = read_jsonl_file(input_jsonl_path)
    existing_results = read_jsonl_file(output_jsonl_path)
    processed_indices = {item['global_id'] for item in existing_results}
    filtered_data = [item for item in input_data if item['global_id'] not in processed_indices]
    skipped_ids = [item['global_id'] for item in input_data if item['global_id'] in processed_indices]
    if skipped_ids:
        pprint(f"Skipping ids: {skipped_ids}")

    with tqdm(total=len(filtered_data), desc="Processing Statements") as pbar:
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
                    batch_results.sort(key=lambda x: x['global_id'])
                    save_results(batch_results, output_jsonl_path)

if __name__ == "__main__":
    input_jsonl_path = '/./PanelTR/sem-tab-fact/data/test_openai.jsonl'
    output_jsonl_path = '/./PanelTR/sem-tab-fact/outputs/single_ds_test_0109_16.jsonl'
    main(input_jsonl_path, output_jsonl_path, batch_size=10)