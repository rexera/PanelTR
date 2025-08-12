import jsonlines
from tqdm import tqdm
from textwrap import dedent
from openai import OpenAI
import os

client = OpenAI()
MODEL = "gpt-4o"

prompt_0_shot = '''
You are an expert in question answering.
You will be given a claim and relevant set of evidence.
Verdict the claim as "SUPPORTS", "REFUTES", or "NOT ENOUGH INFO" based on given evidence.

Your answer format should be:

Analysis:
1.
2.
3.
...

Final Answer: 
(choose from "SUPPORTS", "REFUTES", or "NOT ENOUGH INFO")

'''

prompt='''
You are an expert in question answering.
You will be given a claim and relevant set of evidence.
Verdict the claim as "SUPPORTS", "REFUTES", or "NOT ENOUGH INFO" based on given evidence.

Guidance:
- For a claim to be marked as "SUPPORTS", every piece of information in the claim must be backed by evidence.
- To mark a claim as "REFUTES", you only need to find sufficient evidence that contradicts any part of the claim. Even if the rest of the claim might be accurate, refuting one section is enough.
- A claim is classified as "NOT ENOUGH INFO" if there is not enough information available in the provided evidence to verify or refute it. This typically happens when the relevant data is missing, incomplete, or ambiguous.

Your answer format should be:

Analysis:
1.
2.
3.
...

Final Answer: 
(choose from "SUPPORTS", "REFUTES", or "NOT ENOUGH INFO")

'''

def gpt(input_sentence):
    response = client.chat.completions.create(
        model=MODEL,
        #temperature=1,
        #max_tokens=10,
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
    print(answer)

    # 提取关键词 "Final Answer:" 后面的推断结论
    try:
        # 寻找 "Final Answer:" 位置
        final_answer_index = answer.lower().find("final answer:")

        if final_answer_index != -1:
            # 提取 "Final Answer:" 之后的部分，并去掉前后的空格
            final_inference = answer[final_answer_index + len("final answer:"):].strip().lower()
            # 提取第一个有效单词 (support, refuted, unknown)
            #final_inference = str(final_answer.split()[0:3]).replace('*', '').lower()
            print(f"Extracted Answer: {final_inference}")

            # 确保只返回支持、反驳或未知三者之一
            if final_inference in ['supports', 'refutes', 'not enough info']:
                return final_inference
            else:
                print(f"Unrecognized answer: {final_inference}")
                return "not enough info"
        else:
            print("No 'Final Answer:' found in GPT output.")
            return "not enough info"
    except Exception as e:
        print(f"Error extracting final answer: {e}")
        return "not enough info"



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
    current_id = start_index
    count = 0

    # 过滤从 start_index 开始的数据
    filtered_data = [item for item in input_data if item['index'] >= start_index]

    # 设定 tqdm 进度条，从 start_index 开始
    with tqdm(total=len(input_data), initial=start_index, desc="Processing") as pbar:
        # 遍历过滤后的输入数据
        for item in filtered_data:
            try:
                # 提取输入的 claim 和 evidence 并转换为字符串输入给 GPT
                claim = item['claim']
                evidence = item['evidence']
                input_sentence = f"Claim: {claim}\nEvidence: {evidence}"

                # 调用GPT生成预测
                prediction = gpt(input_sentence)  # gpt()直接返回字符串

                # 将id和prediction保存到predictions列表中
                predictions.append({"index": item['index'], "prediction": prediction})
                current_id += 1
                count += 1

                # 每处理 batch_size 个句子，保存一次结果
                if count % batch_size == 0:
                    save_batch_results(output_jsonl_path, predictions, batch_num)
                    predictions = []  # 清空当前保存的batch
                    batch_num += 1

                # 更新进度条
                pbar.update(1)

            except Exception as e:
                print(f"Error processing item with id {current_id}: {e}")

    # 保存最后未满batch_size的剩余结果
    if predictions:
        save_batch_results(output_jsonl_path, predictions, batch_num)


# 设置输入输出文件路径
input_jsonl_path = '/./feverous/data_openai/feverous_dev_gpt_final_tweaked_w_index.jsonl'  # 输入jsonl文件路径
output_jsonl_path = '/./feverous/output/4o_dev_w_guidance.jsonl'  # 输出jsonl文件路径

if __name__ == "__main__":
    main(input_jsonl_path, output_jsonl_path, batch_size=10, start_index=1880)
