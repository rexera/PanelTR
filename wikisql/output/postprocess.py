import re
import jsonlines

def remove_index_and_save(input_txt_path, output_jsonl_path):
    """读取txt文件，移除index，保留json部分，并写入jsonl文件"""
    with open(input_txt_path, 'r') as infile, jsonlines.open(output_jsonl_path, mode='w') as outfile:
        for line in infile:
            # 使用正则表达式删除前面的 'index: x, ' 部分，保留后面的内容
            match = re.search(r'{.*}', line)
            if match:
                json_content = match.group(0)
                # 将json字符串解析为字典，然后写入jsonl文件
                try:
                    json_obj = eval(json_content)  # 使用 eval 解析字符串为 Python 对象
                    outfile.write(json_obj)
                except Exception as e:
                    print(f"Error processing line: {line}, error: {e}")

if __name__ == "__main__":
    input_txt_path = '/./PanelTR/wikisql/output/4omini_test_straight_0107_17.txt'  # 输入的txt文件路径
    output_jsonl_path = '/./PanelTR/wikisql/output/4omini_test_straight_0107_17_final.jsonl'  # 输出的jsonl文件路径

    remove_index_and_save(input_txt_path, output_jsonl_path)
