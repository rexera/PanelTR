import json
import jsonlines
from tqdm import tqdm
from feverous.database.feverous_db import FeverousDB
from feverous.utils.wiki_page import WikiPage

def extract_page_elements(doc_id, feverous_db):
    """
    提取指定页面中的所有元素并存储为自定义结构（字典）。
    返回：页面中所有元素的ID和内容（字典）。
    """
    page_json = feverous_db.get_doc_json(doc_id)
    if not page_json:
        print(f"Document {doc_id} not found in database.")
        return {}

    wiki_page = WikiPage(doc_id, page_json)
    page_elements = {}

    # 提取标题
    title_content = wiki_page.get_title_content()
    if title_content:
        page_elements[f"{doc_id}_title"] = title_content
    else:
        print(f"Warning: No title found for {doc_id}")

    # 提取所有句子
    sentences = wiki_page.get_sentences()
    for sentence in sentences:
        page_elements[sentence.get_id()] = str(sentence)

    # 提取所有表格及其单元格和标题（caption）
    tables = wiki_page.get_tables()
    for idx, table in enumerate(tables):
        # 提取表格的标题或说明（caption），ID为 doc_table_caption_X
        caption_id = f"{doc_id}_table_caption_{idx}"
        if table.caption:  # 检查表格是否有 caption
            caption_content = table.caption
            page_elements[caption_id] = caption_content
            #print(f"Caption {caption_id} 提取成功: {caption_content}")
        else:
            pass

        # 提取每个表格的单元格
        rows = table.get_rows()
        for row in rows:
            cells = row.get_row_cells()
            for cell in cells:
                page_elements[cell.get_id()] = str(cell)

    # 提取所有列表项（item）
    lists = wiki_page.get_lists()
    for wiki_list in lists:
        for item_id, item_content in wiki_list.list_items.items():
            page_elements[item_id] = str(item_content)

    # 提取所有章节（section）
    sections = wiki_page.get_sections()
    for section in sections:
        page_elements[section.get_id()] = str(section)

    return page_elements


def get_all_doc_ids(json_data):
    """
    从 JSON 的 content 和 context 中提取所有不同的 doc_id。
    """
    doc_ids = set()

    for evidence_item in json_data['evidence']:
        # 从 content 中提取 doc_id
        for content_id in evidence_item['content']:
            doc_id = content_id.split('_')[0]
            doc_ids.add(doc_id)

        # 从 context 中提取 doc_id
        for context_id, context_value in evidence_item['context'].items():
            doc_id = context_id.split('_')[0]
            doc_ids.add(doc_id)

            for val in context_value:
                doc_id = val.split('_')[0]
                doc_ids.add(doc_id)

    return doc_ids


def replace_ids_with_content(json_data, page_elements_dict):
    """
    将 JSON 数据中的所有 ID 替换为自定义结构中的内容，最终 JSON 中没有 ID，只有具体内容。
    page_elements_dict 是一个字典，其中键是 doc_id，值是该 doc_id 对应的页面元素字典。
    """
    for evidence_item in json_data['evidence']:
        # 替换 content 中的ID为实际内容
        new_content = []
        for content_id in evidence_item['content']:
            doc_id = content_id.split('_')[0]  # 提取 doc_id
            stripped_id = content_id.replace(f"{doc_id}_", "")  # 去掉doc_id

            if doc_id in page_elements_dict:
                page_elements = page_elements_dict[doc_id]

                # 替换 content 中的 ID
                if content_id in page_elements:
                    new_content.append(page_elements[content_id])
                elif stripped_id in page_elements:
                    new_content.append(page_elements[stripped_id])
                else:
                    new_content.append(f"Content not found for {content_id}")
            else:
                new_content.append(f"Document {doc_id} not found for {content_id}")

        evidence_item['content'] = new_content

        # 替换 context 中的键和值为实际内容
        new_context = {}
        for context_id, context_values in evidence_item['context'].items():
            doc_id = context_id.split('_')[0]  # 提取 doc_id
            stripped_context_id = context_id.replace(f"{doc_id}_", "")  # 去掉doc_id

            if doc_id in page_elements_dict:
                page_elements = page_elements_dict[doc_id]

                # 替换 context 键的 ID
                if context_id in page_elements:
                    new_context_key = page_elements[context_id]
                elif stripped_context_id in page_elements:
                    new_context_key = page_elements[stripped_context_id]
                else:
                    new_context_key = f"Context not found for {context_id}"

                # 替换 context 值的 ID
                new_context_values = []
                for val in context_values:
                    stripped_val_id = val.replace(f"{doc_id}_", "")  # 去掉doc_id

                    if val in page_elements:
                        new_context_values.append(page_elements[val])
                    elif stripped_val_id in page_elements:
                        new_context_values.append(page_elements[stripped_val_id])
                    else:
                        new_context_values.append(f"Context not found for {val}")

                # 更新新的 context 键值对
                new_context[new_context_key] = new_context_values

        # 将 context 更新为替换后的键和值
        evidence_item['context'] = new_context

    return json_data


def filter_fields(json_data):
    """
    只保留 evidence, content, context, claim, label 这些字段，删除其他字段。
    """
    allowed_keys = ['evidence', 'claim', 'label']
    filtered_data = {key: json_data[key] for key in allowed_keys if key in json_data}
    
    # 确保 evidence 的结构只包含 content 和 context
    for evidence_item in filtered_data.get('evidence', []):
        evidence_item_keys = ['content', 'context']
        for key in list(evidence_item.keys()):
            if key not in evidence_item_keys:
                del evidence_item[key]

    return filtered_data


def process_jsonl(input_file, output_file, feverous_db):
    """
    处理 JSONL 文件，根据页面内容替换 ID，并生成新的 JSONL 文件。
    """
    with jsonlines.open(input_file, 'r') as reader, jsonlines.open(output_file, 'w') as writer:
        # 遍历每个 JSON 对象
        for obj in tqdm(reader):
            # 确保对象是字典
            if not isinstance(obj, dict):
                print(f"Skipping non-dictionary object: {str(obj)[:100]}")
                continue

            # 提取所有涉及的 doc_id
            doc_ids = get_all_doc_ids(obj)

            # 提取所有需要的页面内容，并存储在一个字典中
            page_elements_dict = {}
            for doc_id in doc_ids:
                page_elements = extract_page_elements(doc_id, feverous_db)
                if page_elements:
                    page_elements_dict[doc_id] = page_elements


            # 删除不必要的字段
            obj = filter_fields(obj)   

            # 用页面内容替换原 ID
            obj = replace_ids_with_content(obj, page_elements_dict)

            # 写入修复并处理后的 JSON 对象
            writer.write(obj)


def main():
    # 数据库路径
    wiki_path = "/feverous/data/feverous_wikiv1.db"
    input_file = "/feverous/data/dev.combined.not_precomputed.p5.s5.t3.jsonl"
    output_file = "/feverous/data/data_openai/feverous_openai.jsonl"  # 输出的 jsonl 文件路径

    # 加载 Wikipedia 数据库
    feverous_db = FeverousDB(wiki_path)

    # 处理 JSONL 文件
    process_jsonl(input_file, output_file, feverous_db)

if __name__ == "__main__":
    main()
