import os
import json
import re
import xml.etree.ElementTree as ET
import jsonlines

# 正则表达式模式，用于提取 <statement> 标签中的 id 和 text
statement_pattern = re.compile(r'<statement id="(\d+)" text="(.*?)"\s*type=".*?">')

# 解析并转换XML文件为符合schema的JSON格式，处理每个table并关联statements
def parse_xml_to_json_with_xpath_and_regex(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    xml_id = os.path.splitext(os.path.basename(xml_file))[0]
    tables_data = []
    all_table_elements = root.findall('.//table')

    for table in all_table_elements:
        table_data = {
            "xml_id": xml_id,
            "table_id": table.get('id'),
            "caption": table.find('.//caption').get('text', "") if table.find('.//caption') is not None else "",
            "legend": table.find('.//legend').get('text', "") if table.find('.//legend') is not None else "",
            "footnote": table.find('.//footnote').get('text', "") if table.find('.//footnote') is not None else "",
            "rows": [],
            "statements": []
        }

        for row in table.findall('.//row'):
            row_data = []
            for cell in row.findall('.//cell'):
                text = cell.get('text', "")
                row_data.append(text)
            table_data["rows"].append(row_data)

        table_content = ET.tostring(table, encoding='unicode')
        statements = statement_pattern.findall(table_content)
        table_data["statements"] = [{"id": statement_id, "text": text} for statement_id, text in statements]
        tables_data.append(table_data)

    return tables_data

# 批量处理文件夹中的所有XML文件并保存为JSONL格式，增加 xml_id
def convert_xml_folder_to_jsonl(folder_path):
    jsonl_data = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.xml'):
            file_path = os.path.join(folder_path, file_name)
            print(f"Processing file: {file_path}")
            tables_data = parse_xml_to_json_with_xpath_and_regex(file_path)
            jsonl_data.extend(tables_data)
    return jsonl_data

# 为每个statement添加全局ID并转换为每行一个statement的格式
def transform_to_single_statement_per_line_with_global_id(jsonl_data, output_jsonl_path):
    global_id = 0
    with jsonlines.open(output_jsonl_path, 'w') as writer:
        for obj in jsonl_data:
            xml_id = obj['xml_id']
            table_id = obj['table_id']
            caption = obj['caption']
            legend = obj['legend']
            footnote = obj['footnote']
            rows = obj['rows']
            for statement in obj['statements']:
                statement['global_id'] = global_id
                global_id += 1
                new_obj = {
                    "global_id": statement['global_id'],
                    "xml_id": xml_id,
                    "table_id": table_id,
                    "id": statement['id'],
                    "text": statement['text'],
                    "caption": caption,
                    "legend": legend,
                    "footnote": footnote,
                    "rows": rows
                }
                writer.write(new_obj)

if __name__ == "__main__":
    folder_path = '/./PanelTR/sem-tab-fact/data/test/input'
    final_jsonl_path = '/./PanelTR/sem-tab-fact/data/test_openai.jsonl'

    jsonl_data = convert_xml_folder_to_jsonl(folder_path)
    transform_to_single_statement_per_line_with_global_id(jsonl_data, final_jsonl_path)