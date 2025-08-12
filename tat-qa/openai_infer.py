import re
import json
from tqdm import tqdm
from textwrap import dedent
from openai import OpenAI
import os

client = OpenAI()
MODEL = "gpt-4o"

prompt_old = '''
Based on a given table and some related paragraphs, offer an 'answer' and one relevant 'scale'.

- `answer`: any `float`, `string` or a list with `float` or `string`. could be a sentence 'string'. when impossible to answer, leave blank ("")
- `scale`: `string`. choose from ['thousand', 'million', 'billion', 'percent'] when not applicable, leave blank ("")

Let's do it step by step.
For one question, give a step-wise analysis and two answers in a set format.

For example,

Analysis:

1. ...
2. ...
3. ...
...

Final Answer: 
["answer1", "answer2", "answer3"]
Scale: "thousand"
'''

prompt = '''
Below is an instruction that describes a question answering task in the finance domain, paired with an input table and its relevant text that provide further context. The given question is relevant to the table and text. Generate an appropriate answer to the given question.  

### Instruction 

Given a table and a list of texts in the following, answer the question posed using the following five-step process: 

Step 1: Predict the type of question being asked. Store this prediction in the variable ‘{question_type}‘. The value of ‘{question_type}‘ can be one of the following:‘Single span‘, ‘Multiple spans‘, ‘Count‘, or ‘Arithmetic‘. 
Step 2: Extract the relevant strings or numerical values from the provided table or texts. Store these pieces of evidence in the variable ‘{evidence}‘. If there are multiple pieces of evidence, separate them using the ’#’ symbol. 
Step 3: if the ‘{question_type}‘ is ‘Arithmetic‘, formulate an equation using values stored in ‘{evidence}‘. Store this equation in the variable ‘{equation}‘. For all other question types, set the value of {equation} to ’N.A.’. 
Step 4: Predict or calculate the answer based on the question type, evidence and equation. Store it in the variable ‘{answer}‘. If there are multiple values, separate them using the ’#’ symbol. 
Step 5: If the value of the ‘{answer}‘ is numerical, predict its scale and store it in a variable named ‘{scale}‘. The value of ‘{scale}‘ can be one of the following: ‘none‘, ‘percent‘, ‘thousand‘, ‘million‘, or ‘billion‘. For non-numerical values, leave blank (""). 

Please organize the results in the following table: 

| step | output | 
| 1 | {question_type} | 
| 2 | {evidence} | 
| 3 | {equation} | 
| 4 | {answer} | 
| 5 | {scale} | 

Finally, present the final answer in the format: 

Final Answer: 
["answer1", "answer2", "answer3"]
Scale: "thousand"

'''

def gpt(input_sentence):
    response = client.chat.completions.create(
        model=MODEL,
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
    return answer


def extract_answer_and_scale(gpt_output):
    """ 使用正则表达式提取 'Final Answer' 和 'Scale'，处理带逗号的数字或字符串 """
    try:
        # 匹配 'Final Answer'，优先匹配列表格式的答案
        list_match = re.search(r'Final Answer:\s*\[(.*?)\]', gpt_output)
        if list_match:
            final_answer = list_match.group(1).strip()
            # 匹配带逗号的数字（"$1,496.5"）或者普通字符串，并将其放入列表中
            final_answer_list = re.findall(r'\"(.*?)\"', final_answer)
        else:
            # 如果没有列表，匹配单个字符串或者数字
            single_match = re.search(r'Final Answer:\s*(["\'][^"\']+["\']|\d+(\.\d+)?)', gpt_output)
            final_answer_list = [single_match.group(1).strip().strip('"').strip("'")] if single_match else [""]

        # 提取 Scale
        scale_match = re.search(r'Scale:\s*"([^"]*)"', gpt_output)
        scale = scale_match.group(1).strip() if scale_match else ""

        return final_answer_list, scale
    except Exception as e:
        print(f"Error extracting answer and scale: {e}")
        return [""], ""


def load_existing_results(filename):
    """检查文件是否存在，存在则加载，否则返回一个空字典"""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}


def save_results(results, filename):
    """将结果保存到指定的 JSON 文件（根据 index）"""
    existing_results = load_existing_results(filename)  # 读取现有文件内容

    # 确保新结果根据 index 追加不覆盖已有的键值对
    for uid, value in results.items():
        # 根据问题的 index 判断，确保新结果只追加不覆盖
        index = value[0]  # 第一个元素是问题的 index
        if index not in [v[0] for v in existing_results.values()]:
            existing_results[uid] = value  # 只追加新的键值对

    # 覆盖写入整个大字典
    with open(filename, 'w') as outfile:
        json.dump(existing_results, outfile, indent=4)


def process_data(data, output_file, batch_size=10, start_index=0):
    """处理数据并逐步保存结果"""
    gpt_results = {}  # 用于存储批处理的结果
    batch_num = 1  # 批次编号
    count = 0  # 当前批次处理的问题数量

    # 先计算所有问题的总数量，以便在外部使用 tqdm 进度条
    all_questions = [
        question for item in data if isinstance(item, dict) and 'questions' in item
        for question in item['questions']
    ]

    try:
        with tqdm(total=len(all_questions), desc="Processing all questions") as pbar:
            # 更新进度条以跳过已处理的问题
            pbar.update(start_index)

            for item in data:
                if isinstance(item, dict) and 'questions' in item:
                    for question in item['questions']:
                        # 跳过 index 小于 start_index 的问题
                        if 'index' in question and question['index'] < start_index:
                            continue

                        # 提取问题信息
                        question_uid = question['uid']
                        question_text = question['question']
                        question_index = question['index']  # 获取 question 的 index

                        # 提取表格和段落信息
                        table_data = item['table']['table']
                        paragraphs = [p['text'] for p in item['paragraphs']]

                        # 生成输入文本
                        gpt_input = f"Table:\n{table_data}\nParagraphs:\n{paragraphs}\nQuestion:\n{question_text}\n"

                        try:
                            # 调用 GPT 接口生成答案
                            gpt_output = gpt(gpt_input)

                            # 使用正则表达式提取 'Final Answer' 和 'Scale'
                            final_answer, scale = extract_answer_and_scale(gpt_output)

                            # 将结果保存为 {实际 uid: [index, [answer1, answer2], scale]}
                            gpt_results[question_uid] = [
                                question_index,
                                final_answer,  # 将 answer 放入列表
                                scale
                            ]

                            print(f"\n Extracted:\n{gpt_results[question_uid]}")

                            count += 1  # 增加处理的问题计数

                            # 每处理 batch_size 个问题，保存一次结果
                            if count % batch_size == 0:
                                save_results(gpt_results, output_file)
                                print(f"Saved batch {batch_num} to {output_file}")
                                batch_num += 1
                                gpt_results = {}  # 清空当前批处理的结果

                            # 更新进度条
                            pbar.update(1)

                        except Exception as e:
                            print(f"Error processing question {question_uid}: {e}")

    except Exception as main_exception:
        print(f"Processing interrupted due to: {main_exception}")

    # 最后保存剩余的结果（如果有未保存的批次）
    if gpt_results:
        save_results(gpt_results, output_file)
        print(f"Saved the remaining results to {output_file}")


def main():
    # 设置输入文件路径
    input_file_path = '/./PanelTR/tat-qa/dataset_raw/tatqa_dataset_dev_w_index.json'

    # 设置保存结果的文件路径
    output_file_path = '/./PanelTR/tat-qa/output/4o_dev_pipe.json'

    # 设置批处理大小
    batch_size = 10

    # 读取 JSON 文件
    with open(input_file_path, 'r') as file:
        data = json.load(file)

    # 调用处理函数，从start_index开始
    process_data(data, output_file_path, batch_size=batch_size, start_index=0)


if __name__ == "__main__":
    main()
