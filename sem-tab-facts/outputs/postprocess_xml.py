import os
import json
import re

# 定义文件路径
jsonl_file = '/./PanelTR/sem-tab-fact/outputs/single_ds_test_0109_16.jsonl'
xml_folder = '/./PanelTR/sem-tab-fact/data/test/input'
output_folder = '/./PanelTR/sem-tab-fact/outputs/single_ds_test_0109_16'

# 确保输出文件夹存在
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 读取JSONL文件
with open(jsonl_file, 'r', encoding='utf-8') as f:
    jsonl_records = [json.loads(line) for line in f]

# 遍历每一条记录，按文件分组
file_updates = {}

# 收集所有需要更新的内容
for record in jsonl_records:
    #xml_id = record['xml_id']
    xml_id = record.get('xml_id')
    if xml_id is None:
        print(f"Record missing 'xml_id': {record}")
        continue
    table_id = record['table_id']  # 读取table_id
    statement_id = str(record['statement_id'])  # 确保 statement_id 是字符串类型
    new_type = record['type']

    # 构建xml文件的路径
    xml_file = os.path.join(xml_folder, f'{xml_id}.xml')

    # 检查xml文件是否存在
    if not os.path.exists(xml_file):
        print(f"XML file {xml_file} not found, skipping...")
        continue

    # 如果这个文件之前没有读取过，先读取
    if xml_id not in file_updates:
        with open(xml_file, 'r', encoding='utf-8') as file:
            xml_content = file.read()
        file_updates[xml_id] = xml_content

    # 获取当前文件的内容
    xml_content = file_updates[xml_id]

    # 改进正则表达式，确保匹配table_id、statement_id，并替换type
    pattern_table = rf'(<table[^>]*id="{table_id}"[^>]*>.*?</table>)'  # 匹配整个table段落
    match_table = re.search(pattern_table, xml_content, re.DOTALL)

    if match_table:
        table_content = match_table.group(1)  # 获取匹配到的table内容
        #print(f"Found table {table_id} in {xml_id}")

        # 在匹配到的table内容中查找statement
        pattern_statement = rf'(<statement\s+id="{statement_id}"[^>]*\btype=")(.*?)(")'
        match_statement = re.search(pattern_statement, table_content)

        if match_statement:
            #print(f"Found statement {statement_id} in table {table_id} of {xml_id}, updating type to {new_type}")
            #print(f"Before update: {match_statement.group(0)}")

            # 使用正则替换 type 的值
            updated_table_content = re.sub(pattern_statement, rf'\1{new_type}\3', table_content)

            # 替换整个table段落
            updated_content = xml_content.replace(table_content, updated_table_content)

            # 更新文件内容
            file_updates[xml_id] = updated_content
        else:
            print(f"Statement id {statement_id} not found in table {table_id} of {xml_id}, skipping...")
    else:
        print(f"Table id {table_id} not found in {xml_id}, skipping...")

# 将更新后的内容保存到新的文件
for xml_id, updated_content in file_updates.items():
    output_file = os.path.join(output_folder, f'{xml_id}.xml')

    try:
        # 写入更新后的内容
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(updated_content)
            #print(f"File {output_file} successfully written with updated content.")

        # 重新读取写入的文件，确认保存是否成功
        with open(output_file, 'r', encoding='utf-8') as file:
            final_content = file.read()
            # 这里检查该文件的每条语句的正确性
            for record in jsonl_records:
                if record['xml_id'] == xml_id:
                    statement_id = str(record['statement_id'])
                    table_id = record['table_id']
                    new_type = record['type']
                    # 检查是否在正确的table和statement中更新了type
                    pattern_verify = rf'<table[^>]*id="{table_id}".*?<statement\s+id="{statement_id}"[^>]*\btype="{new_type}".*?</table>'
                    if not re.search(pattern_verify, final_content, re.DOTALL):
                        print(
                            f"Verification failed: {xml_id} table {table_id} statement {statement_id} not correctly written.")
                    #else:
                        #print(f"Verification successful: {xml_id} table {table_id} statement {statement_id} correctly written.")

    except Exception as e:
        print(f"Failed to write to {output_file}: {e}")

#print("Process completed.")
