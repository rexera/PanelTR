import os
from datetime import datetime
from pprint import pprint
from textwrap import dedent

import jsonlines
from openai import OpenAI
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Lock
from dotenv import load_dotenv
load_dotenv()

save_lock = Lock()
#timestamp = datetime.now().strftime("%m%d_%H%M")

system_prompt_0_shot = '''
Based on the given table and relevant texts, determine whether a statement is **entailed**, **refuted**, or **unknown**.

"entailed": you can directly or indirectly extract info and decide on its being entailed.
"refuted": there is information about the statement that offers you reasons to refute it.
"unknown": when in some cases, the statement cannot be determined from the table or there is insufficient information to make a determination.

Final Response Format:(make sure you write out the indicator "Final Answer:")

Analysis:
1.
2.
...

Final Answer:
(choose from entailed/refuted/unknown)
'''

system_prompt = '''
Based on the given table and relevant texts, determine whether a statement is **entailed**, **refuted**, or **unknown**.

"entailed": you can directly or indirectly extract info and decide on its being entailed.
"refuted": there is information about the statement that offers you reasons to refute it.
"unknown": when in some cases, the statement cannot be determined from the table or there is insufficient information to make a determination.

Give your answer straight out. No intermediate steps needed.
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

client = OpenAI()
MODEL = "gpt-4o"

'''client = OpenAI(api_key="sk-e86c72ef8f7246d1b695fefa9e261459", base_url="https://api.deepseek.com")
MODEL = "deepseek-chat"'''

def gpt(table, notes, statement):
    # 根据表格、注释、陈述重组 prompt
    prompt = prompt_template.format(
        table=table,
        notes=notes,
        statement=statement
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": dedent(system_prompt)
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    # 提取模型的完整回答（包含步骤和最终推断）
    answer = response.choices[0].message.content
    print(answer)

    # 提取关键词 "Final Answer:" 后面的推断结论
    try:
        # 寻找 "Final Answer:" 位置
        final_answer_index = answer.lower().find("final answer:")

        if final_answer_index != -1:
            # 提取 "Final Answer:" 之后的部分，并去掉前后的空格
            final_answer = answer[final_answer_index + len("final answer:"):].strip()
            # 提取第一个有效单词 (support, refuted, unknown)
            final_inference = final_answer.split()[0].replace('*', '').lower()
            print(f"Extracted Answer: {final_inference}")

            # 确保只返回支持、反驳或未知三者之一
            if final_inference in ['entailed', 'refuted', 'unknown']:
                return final_inference
            else:
                print(f"Unrecognized answer: {final_inference}")
                return "unknown"
        else:
            print("No 'Final Answer:' found in GPT output.")
            return "unknown"
    except Exception as e:
        print(f"Error extracting final answer: {e}")
        return "unknown"

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
    output_jsonl_path = f'/./PanelTR/sem-tab-fact/outputs/4o_test_0107_16_straightout.jsonl'
    main(input_jsonl_path, output_jsonl_path, batch_size=10)