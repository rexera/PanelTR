import json

def transform_evidence():
    """Transform evidence format from nested structure to string format"""
    with open('feverous/data_openai/feverous_openai.jsonl', 'r', encoding='utf-8') as infile, \
         open('feverous/data_openai/feverous_openai_final.jsonl', 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            # Parse JSON object
            obj = json.loads(line.strip())
            
            # Transform evidence format
            if 'evidence' in obj:
                # Convert evidence array to string format
                evidence_str = "[Content:] "
                for ev in obj['evidence']:
                    if 'content' in ev:
                        evidence_str += ' '.join(ev['content']) + ' '
                    if 'context' in ev:
                        evidence_str += "[Context:] "
                        for k, v in ev['context'].items():
                            evidence_str += f"{k} {' '.join(v)} "
                
                # Replace evidence field with string
                obj['evidence'] = evidence_str.strip()
            
            # Write transformed object
            outfile.write(json.dumps(obj, ensure_ascii=False) + '\n')

def add_index():
    """Add index field to each JSON object"""
    with open('feverous/data_openai/feverous_openai.jsonl', 'r', encoding='utf-8') as infile, \
         open('feverous/data_openai/feverous_openai_final.jsonl', 'w', encoding='utf-8') as outfile:
        
        for i, line in enumerate(infile, 1):
            obj = json.loads(line.strip())
            obj['id'] = i
            outfile.write(json.dumps(obj, ensure_ascii=False) + '\n')

def main():
    print("Transforming evidence format...")
    transform_evidence()
    print("Adding indices...")
    add_index()
    print("Done!")

if __name__ == '__main__':
    main() 