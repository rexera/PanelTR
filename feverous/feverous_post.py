import json

# 读取A文件
def read_jsonl_file(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            data.append(json.loads(line.strip()))
    return data

# 写入JSONL文件
def write_jsonl_file(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        for item in data:
            file.write(json.dumps(item, ensure_ascii=False) + '\n')

# 替换prediction
def replace_predictions(a_file, b_file, output_file):
    # 读取A和B文件
    a_data = read_jsonl_file(a_file)
    b_data = read_jsonl_file(b_file)

    '''# 确保A和B文件的行数相同
    if len(a_data) != len(b_data):
        raise ValueError("A文件和B文件的行数不一致，无法进行替换。")'''

    # 遍历并替换B文件中的prediction，但A文件第1行对应到B文件第2行
    for i in range(len(a_data)):
        # 确保 B 文件有足够的行数
        if i + 1 >= len(b_data):
            print(f"警告：B文件的行数不足，无法匹配A文件的第{i + 1}行")
            break

        if 'prediction' in a_data[i]:
            prediction = a_data[i]['prediction'].upper()
            # 检查B文件中第i+1行是否存在prediction键
            if 'predicted_label' in b_data[i + 1]:
                b_data[i + 1]['predicted_label'] = prediction
            else:
                # 如果B文件中没有predicted_label，添加它
                b_data[i + 1]['predicted_label'] = prediction
        else:
            print(f"警告：A文件的第{i + 1}行没有'prediction'字段，跳过该行。")

    # 将替换后的内容写入输出文件
    write_jsonl_file(b_data, output_file)

prediction_file = '/./PanelTR/feverous/output/single_ds_0108_16.jsonl'
template_file = '/./PanelTR/feverous/baseline_output/dev.combined.not_precomputed.p5.s5.t3.cells.verdict.jsonl'
output_file = '/./PanelTR/feverous/output/single_ds_0108_16_final.jsonl'

replace_predictions(prediction_file, template_file, output_file)
