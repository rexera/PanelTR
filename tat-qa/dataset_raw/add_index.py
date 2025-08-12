import json

def add_index_to_questions(json_data):
    global_index = 0  # 全局计数器，从0开始
    # 遍历整个json文件中的所有对象
    for obj in json_data:
        # 遍历每个对象中的questions列表
        for question in obj.get('questions', []):
            # 为每个问题添加index字段，并使用全局计数器
            question['index'] = global_index
            global_index += 1  # 累加全局计数器
    return json_data

def main(input_path, output_path):
    # 加载json文件
    with open(input_path, 'r') as f:
        data = json.load(f)

    # 调用函数为questions添加index字段
    updated_data = add_index_to_questions(data)

    # 将更新后的json数据写回到文件
    with open(output_path, 'w') as f:
        json.dump(updated_data, f, indent=4)

    print(f"Index字段已成功添加到questions中，并保存到 {output_path}")

if __name__ == "__main__":
    input_path = './tatqa_dataset_test_gold.json'
    output_path = './tatqa_dataset_test_gold_w_index.json'
    main(input_path, output_path)
