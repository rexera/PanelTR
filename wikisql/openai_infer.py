import jsonlines
from tqdm import tqdm
from textwrap import dedent
from openai import OpenAI
import os

client = OpenAI()
MODEL = "gpt-4o"

prompt = '''
Based on the given table, transform the question into SQL queries about the table.
Answer in one single jsonline (No ```json``` wrapping):

{"query": {"sel": , "agg": , "conds": [[ ,  , " "]]}}

where:

- `sel`: int. index of the column you select. You can find the actual column from the table.
- `agg`: int. index of the operator you use from aggregation operator list. agg_ops = {'': 0, 'MAX': 1, 'MIN': 2, 'COUNT':3, 'SUM':4, 'AVG':5}
- `conds`: a list of triplets `(column_index, operator_index, condition)` where:
  - `column_index`: int. index of the column you select. You can find the actual column from the table.
  - `operator_index`: int. index of the operator you use from condition operator list. cond_ops = {'=': 0, '>': 1, '<': 2, 'OP': 3}.
  - `condition`: `string` or `float`. the comparison value for the condition.
'''

def gpt(input_sentence):
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": dedent(prompt)
            },
            {
                "role": "user",
                "content": input_sentence
            }
        ],
    )
    answer = response.choices[0].message.content
    answer = answer.lower()  # 将输出内容转换为小写
    print(answer)
    return answer

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

def read_dev_data(dev_file_path):
    """读取dev.jsonl文件数据"""
    data = []
    with jsonlines.open(dev_file_path, 'r') as reader:
        for obj in reader:
            data.append(obj)
    return data

def write_txt_file(file_path, data):
    """将结果追加写入txt文件，一行一个结果，带有index前缀"""
    with open(file_path, 'a') as writer:  # 改为 'a' 模式，确保是追加写入
        for entry in data:
            writer.write(f"{entry}\n")  # 写入一行，换行符

def save_batch_results(output_txt_path, results_with_index, batch_num):
    """保存部分结果到一个txt文件"""
    write_txt_file(output_txt_path, results_with_index)
    print(f"Saved batch {batch_num} to {output_txt_path}")

def main(dev_file_path, table_file_path, output_txt_path, batch_size=50, start_index=1):
    # 读取表格数据和dev文件数据
    table_data = read_table_data(table_file_path)
    dev_data = read_dev_data(dev_file_path)

    # 初始化结果列表和相关计数器
    predictions_with_index = []
    batch_num = 1
    count = 0

    # 设定 tqdm 进度条
    with tqdm(total=len(dev_data), initial=start_index, desc="Processing") as pbar:
        # 从start_index开始处理
        for item in dev_data[start_index:]:
            try:
                # 提取 question 和对应的 table_id
                question = item['question']
                table_id = item['table_id']
                index = item['index']  # 获取index

                # 打印正在处理的table_id
                print(f"Looking for table with id {table_id}, index: {index}")

                # 根据 table_id 查找对应的表格信息
                table_info = table_data.get(table_id)
                if not table_info:
                    print(f"Table with id {table_id} not found for index {index}.")
                    continue

                # 将表格信息和问题一起输入给 GPT
                input_sentence = f"Table: {table_info}\nQuestion: {question}"

                # 调用GPT生成预测
                prediction = gpt(input_sentence)

                # 将结果按index拼接成字符串
                result_with_index = f"index: {index}, {prediction}"

                # 添加到输出结果列表
                predictions_with_index.append(result_with_index)

                count += 1

                # 每处理 batch_size 个句子，保存一次结果
                if count % batch_size == 0:
                    save_batch_results(output_txt_path, predictions_with_index, batch_num)
                    predictions_with_index = []  # 清空当前保存的batch
                    batch_num += 1

                # 更新进度条
                pbar.update(1)

            except Exception as e:
                print(f"Error processing item with id {index}: {e}")

    # 保存最后未满batch_size的剩余结果
    if predictions_with_index:
        save_batch_results(output_txt_path, predictions_with_index, batch_num)


# 设置输入输出文件路径
dev_file_path = '/./WikiSQL/data/test_w_index.jsonl'  # 输入dev.jsonl文件路径
table_file_path = '/./WikiSQL/data/test.tables.jsonl'  # 输入表格文件路径
output_txt_path = '/./WikiSQL/output/4o_test_with_index.txt'  # 输出txt文件

if __name__ == "__main__":
    main(dev_file_path, table_file_path, output_txt_path, batch_size=10, start_index=3687)
