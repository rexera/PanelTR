import os
from datetime import datetime
from pprint import pprint

import jsonlines
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Lock
from paneltr_module.group import paneltr_integrated
import re

prompt = '''
Task Description:

Based on the given table, **translate the question into SQL queries** about the table.
Answer in this following format (must be two lines):
one indicator line ("Final Answer:") + one single jsonline (No ```json``` wrapping):

Final Answer:\n
{"query": {"sel": , "agg": , "conds": [[ ,  , " "]]}}

where:

- `sel`: int. index of the column you select. You can find the actual column from the table.
- `agg`: int. index of the operator you use from aggregation operator list. agg_ops = {'': 0, 'MAX': 1, 'MIN': 2, 'COUNT':3, 'SUM':4, 'AVG':5}
- `conds`: a list of triplets `(column_index, operator_index, condition)` where:
  - `column_index`: int. index of the column you select. You can find the actual column from the table.
  - `operator_index`: int. index of the operator you use from condition operator list. cond_ops = {'=': 0, '>': 1, '<': 2, 'OP': 3}.
  - `condition`: `string` or `float`. the comparison value for the condition.
'''

lock = Lock()
#timestamp = datetime.now().strftime("%m%d_%H%M")


def gpt(input_sentence):
    answer, collaboration = paneltr_integrated(prompt, input_sentence)
    last_line = answer.strip().split('\n')[-1]
    match = re.search(r'\{.*\}', last_line.lower(), re.DOTALL)
    if match:
        line = match.group(0)
        print(f"Extracted: {line}")
        return line
    else:
        return str(collaboration)

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

def read_table_data(table_file_path):
    """读取表格信息并存储为字典，键为table_id"""
    table_data = {}
    try:
        with jsonlines.open(table_file_path, 'r') as reader:
            for obj in reader:
                table_id = obj.get("id")  # 获取表格的 id 字段
                if table_id:
                    table_data[table_id] = obj  # 将表格存入字典
    except Exception as e:
        print(f"Error reading table data: {e}")
    return table_data

def save_results(results, output_txt_path):
    with lock:
        with open(output_txt_path, 'a') as writer:
            for result in results:
                writer.write(f"{result}\n")
        print(f"Results saved to {output_txt_path}")

def process_item(item, table_data):
    try:
        question = item['question']
        table_id = item['table_id']
        index = item['index']

        table_info = table_data.get(table_id)
        if not table_info:
            return None

        input_sentence = f"Table: {table_info}\nQuestion: {question}"
        prediction = gpt(input_sentence)
        result_with_index = f"index: {index}, {prediction}"
        return result_with_index
    except Exception as e:
        print(f"Error processing item with id {index}: {e}")
        return None

def main(dev_file_path, table_file_path, output_txt_path, batch_size=10):
    table_data = read_table_data(table_file_path)
    dev_data = read_jsonl_file(dev_file_path)
    existing_results = []
    if os.path.exists(output_txt_path):
        with open(output_txt_path, 'r') as file:
            for line in file:
                match = re.search(r'index: (\d+)', line)
                if match:
                    existing_results.append(int(match.group(1)))
    processed_indices = set(existing_results)
    filtered_data = [item for item in dev_data if item['index'] not in processed_indices]
    skipped_ids = [item['index'] for item in dev_data if item['index'] in processed_indices]
    if skipped_ids:
        pprint(f"Skipping ids: {skipped_ids}")

    with tqdm(total=len(filtered_data), desc="Processing") as pbar:
        for i in range(0, len(filtered_data), batch_size):
            batch = filtered_data[i:i + batch_size]
            with ProcessPoolExecutor(max_workers=batch_size) as executor:
                future_to_item = {executor.submit(process_item, item, table_data): item for item in batch}
                batch_results = []
                for future in as_completed(future_to_item):
                    result = future.result()
                    if result:
                        batch_results.append(result)
                    pbar.update(1)
                if batch_results:
                    batch_results.sort(key=lambda x: int(re.search(r'index: (\d+)', x).group(1)))
                    save_results(batch_results, output_txt_path)

if __name__ == "__main__":
    dev_file_path = '/./PanelTR/wikisql/data/test_w_index.jsonl'
    table_file_path = '/./PanelTR/wikisql/data/test.tables.jsonl'
    output_txt_path = '/./PanelTR/wikisql/output/MAS_ds_test_0109_17.txt'
    main(dev_file_path, table_file_path, output_txt_path, batch_size=10)