import jsonlines
from tqdm import tqdm
from textwrap import dedent
from openai import OpenAI
import os

client = OpenAI()
MODEL = "gpt-4o"

# 固定的 GPT prompt，用于要求模型根据表格推断 statement
system_prompt = '''
Based on the given table and relevant texts, infer whether a statement is entailed, refuted, or unknown.

"entailed": you can directly or indirectly extract info and decide on its being entailed.
"refuted": there is information about the statement that offers you reasons to refute it.
"unknown": when in some cases, the statement cannot be determined from the table or there is insufficient information to make a determination.

Let's think and answer step by step like this:

1. ...
2. ...
3. ...
...

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
    # 根据表格、注释、陈述重组 prompt
    prompt = prompt_template.format(
        table=table,
        notes=notes,
        statement=statement
    )
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
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
    """逐行读取jsonl文件"""
    data = []
    with jsonlines.open(file_path, 'r') as reader:
        for obj in reader:
            data.append(obj)
    return data

def write_jsonl_file(file_path, data, append=False):
    """逐行写入jsonl文件，支持追加写入"""
    mode = 'a' if append else 'w'
    with jsonlines.open(file_path, mode=mode) as writer:
        for entry in data:
            writer.write(entry)

def save_batch_results(output_jsonl_path, results, batch_num):
    """保存部分结果到jsonl文件"""
    write_jsonl_file(output_jsonl_path, results, append=True)
    print(f"Saved batch {batch_num} to {output_jsonl_path}")


def main(input_jsonl_path, output_jsonl_path, batch_size=10, start_index=0):
    # 读取jsonl文件
    input_data = read_jsonl_file(input_jsonl_path)

    # 初始化结果列表和相关计数器
    predictions = []
    batch_num = 1
    count = 0  # 全局 statement 计数器

    # 计算所有 statement 的总数，并用于进度条
    total_statements = sum(len(item['statements']) for item in input_data)

    # 初始化 tqdm 进度条，设置总数为 statement 的总数量
    with tqdm(total=total_statements, initial=start_index, desc="Processing Statements") as pbar:
        # 遍历所有的输入数据（每行可能包含多个 table 和 statement）
        for item in input_data:
            try:
                # 提取表格、table_id 和 statement 相关信息
                xml_id = item['xml_id']
                table_id = item.get('table_id', '')  # 获取 table_id，假设它是唯一标识符
                table = item['rows']
                table_rows = "\n".join([", ".join(row) for row in table])  # 格式化表格行
                table_content = f"Caption: {item['caption']}\nRows:\n{table_rows}"
                notes = f"Legend: {item.get('legend', '')}\nFootnote: {item.get('footnote', '')}"

                # 遍历每个 statement 进行推断
                for statement_obj in item['statements']:
                    count += 1  # 全局 statement 计数增加

                    # 如果当前 statement 的计数小于 start_index，跳过该 statement
                    if count < start_index:
                        continue

                    statement_id = statement_obj['id']
                    statement = statement_obj['text']

                    # 调用 GPT 进行推理
                    prediction_type = gpt(table_content, notes, statement)

                    # 保存当前 statement 的推断结果，加入 table_id 字段
                    predictions.append({
                        "xml_id": xml_id,
                        "table_id": table_id,
                        "statement_id": statement_id,
                        "type": prediction_type
                    })

                    # 每处理 batch_size 个句子，保存一次结果
                    if count % batch_size == 0:
                        save_batch_results(output_jsonl_path, predictions, batch_num)
                        predictions = []  # 清空当前保存的 batch
                        batch_num += 1

                    # 更新进度条，按每个 statement 更新
                    pbar.update(1)

            except Exception as e:
                print(f"Error processing item with xml_id {xml_id}: {e}")

    # 保存最后未满 batch_size 的剩余结果
    if predictions:
        save_batch_results(output_jsonl_path, predictions, batch_num)

# 设置输入输出文件路径
input_jsonl_path = '/./PanelTR/sem-tab-fact/data/test_openai_new.jsonl'  # 输入jsonl文件路径
output_jsonl_path = '/./PanelTR/sem-tab-fact/outputs/4o_test_1122.jsonl'  # 输出jsonl文件路径

if __name__ == "__main__":
    main(input_jsonl_path, output_jsonl_path, batch_size=10, start_index=0)
