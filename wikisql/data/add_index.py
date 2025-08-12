import json

# 读取原始 JSONL 文件并在每个对象的开头添加 index 字段
def add_index_to_jsonl(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for index, line in enumerate(infile):
            json_obj = json.loads(line.strip())  # 将每一行解析为 JSON 对象
            # 创建一个新的字典，并把 index 放到第一个位置
            new_json_obj = {'index': index}
            new_json_obj.update(json_obj)  # 把原来的数据合并到新的字典里
            outfile.write(json.dumps(new_json_obj) + '\n')  # 写回文件，转换为 JSON 格式并换行

# 使用示例
input_file = '/./WikiSQL/data/test.jsonl'
output_file = '/./WikiSQL/data/test_w_index.jsonl'
add_index_to_jsonl(input_file, output_file)
