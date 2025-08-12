# FEVEROUS, in PanelTR

[FEVEROUS: Fact Extraction and VERification Over
Unstructured and Structured information](https://arxiv.org/pdf/2106.05707.pdf).

## Main Focus

Verdict a statement as "supports", "refutes", or "not enough info" based on table and context.

**Original Work:**
- Stage 1: Retrieve
- Stage 2: Verdict

**Our Focus:**

Based on the **retrieved tabular and textual data**, models verdict.

## Prepare Data

Call the following script to download the FEVEROUS data:

```bash
./scripts/download_data.sh
```

Or you can download the data from the [FEVEROUS dataset page](https://fever.ai/dataset/feverous.html) directly. Namely:

* Training Data
* Development Data
* Wikipedia Data as a database (sqlite3)

After downloading the data, unpack the Wikipedia data into the same folder (i.e. `data`).

## Read Annotations

> This section offers code-level instruction on how to read/extract data from annotations. It's really mind-boggling.
> 
> Refer to the original [README](https://github.com/Raldir/FEVEROUS/blob/main/README.md) for that. Here I omitted it.
> 
> Refer to https://fever.ai/dataset/feverous.html for schema note.


## Data Preprocessing

1. [Download FEVEROUS baseline output](https://github.com/Raldir/FEVEROUS/tree/main/baseline_output) and put it in `baseline_output` folder.

2. Later we start with `baseline_output/dev.combined.not_precomputed.p5.s5.t3.cells.verdict`.

```json
# data demo
{"evidence": [{"content": ["Al Stokes_cell_0_7_1", "Al Stokes_cell_0_8_1"], "context": {"Al Stokes_cell_0_7_1": ["Al Stokes_title", "Al Stokes_header_cell_0_7_0", "Al Stokes_header_cell_0_5_0", "Al Stokes_header_cell_0_4_0", "Al Stokes_header_cell_0_3_0"], "Al Stokes_cell_0_8_1": ["Al Stokes_title", "Al Stokes_header_cell_0_8_0", "Al Stokes_header_cell_0_5_0", "Al Stokes_header_cell_0_4_0", "Al Stokes_header_cell_0_3_0"]}}], "id": 9727, "claim": "Al Stokes had more home runs than than runs batted in.", "label": "REFUTES", "annotator_operations": [{"operation": "start", "value": "start", "time": "0"}, {"operation": "Now on", "value": "undefined", "time": "0.001"}, {"operation": "search", "value": "Al Stokes", "time": "0.022"}, {"operation": "Now on", "value": "Al Stokes", "time": "0.023"}, {"operation": "Highlighting", "value": "Al Stokes_cell_0_7_1", "time": "0.03"}, {"operation": "Highlighting", "value": "Al Stokes_cell_0_8_1", "time": "0.031"}, {"operation": "finish", "value": "finish", "time": "0.054"}, {"operation": "Now on", "value": "Al Stokes", "time": "1619138938.376"}, {"operation": "finish", "value": "finish", "time": "1619138942.255"}], "predicted_evidence": ["Aubrey Huff_sentence_36", "Al Stokes_sentence_1", "Aubrey Huff_sentence_89", "Al Stokes_sentence_3", "Aubrey Huff_sentence_6", "Al Stokes_header_cell_0_0_0", "Al Stokes_header_cell_0_0_0", "Al Stokes_cell_0_1_0", "Al Stokes_cell_0_1_0", "Al Stokes_cell_0_2_0", "Al Stokes_cell_0_2_1", "Al Stokes_cell_0_7_1", "Al Stokes_header_cell_0_8_0", "Al Stokes_cell_0_8_1"], "predicted_label": "REFUTES"}
```

3. Your prediction submission (i.e. file fed into `eval.sh` script) should resemble `baseline_output/dev.combined.not_precomputed.p5.s5.t3.cells.verdict.submission.jsonl`

4. Simply feed `baseline_output/dev.combined.not_precomputed.p5.s5.t3.cells.verdict.jsonl` into `data/data_openai/data_extract.py` and get a file ready for postprocessing. (Like: `data/data_openai/feverous_openai.jsonl`)

### `data_extract.py` was a HARD TOIL. It worths a boast.

The file in `baseline_output` offers only indices of table elements. Each type of element has its unique method to extract yet no one ever wrote this indispensable intermediate script. I did it from scratch.

```json
# data demo
{"evidence": [{"content": ["0", "7"], "context": {"0": ["Al Stokes", "[H] Home runs", "[H] MLB statistics", "[H] Last MLB appearance", "[H] MLB debut"], "7": ["Al Stokes", "[H] [[Run_batted_in|Runs batted in]]", "[H] MLB statistics", "[H] Last MLB appearance", "[H] MLB debut"]}}], "claim": "Al Stokes had more home runs than than runs batted in.", "label": "REFUTES"}
```

5. Feed `data/data_openai/feverous_openai.jsonl` into `data/data_openai/data_post.py` and get a file that can be directly fed to model. (Like: `data/data_openai/feverous_openai_final.jsonl`)

```json
# data demo
{"index": 19, "claim": "Al Stokes had more home runs than than runs batted in.", "evidence": "[Content:] 0 7 [Context:] 0 Al Stokes [H] Home runs [H] MLB statistics [H] Last MLB appearance [H] MLB debut 7 Al Stokes [H] [[Run_batted_in|Runs batted in]] [H] MLB statistics [H] Last MLB appearance [H] MLB debut", "id": 20, "label": "REFUTES"}
```

## Inference

### 1. Data Needed

---

`data_openai/feverous_openai_final.jsonl` 

Extracted from Wiki Database. With `claim` and `evidence` (including flattened `content` and `context`) in Natural Language, `predicted_evidence` for retrieving stage in original work (which is neglected and set baseline), and of course `label`.

---

`baseline_output/dev.combined.not_precomputed.p5.s5.t3.cells.verdict.jsonl`

FEVEROUS baseline verdict result. Includes: `claim, evidence, label, predicted_evidence, predicted_label`. The complete baseline result for two stages (retrieve and fact verification)

### 2. Inference & Postprocessing

## Inference

```
openai_infer.py  # vanilla
openai_infer_parallel.py # vanilla parallel
openai_infer_single_parallel.py # single-agent parallel
openai_infer_mas_parallel.py # multi-agent parallel
```

Prediction results are stored in `output/`.

```json
# inference demo
{"index": 19, "prediction": "refutes"}
```

## Postprocessing

`feverous_post.py`

This replaces the `predicted_label` in `dev.combined.not_precomputed.p5.s5.t3.cells.verdict.jsonl`, with `predicted_label` in GPT results (something like `output/4o.jsonl`), for a direct negligence of retrieval stage and the evaluation of reasoning stage.

```json
# postprocessing demo
{"evidence": [{"content": ["Al Stokes_cell_0_7_1", "Al Stokes_cell_0_8_1"], "context": {"Al Stokes_cell_0_7_1": ["Al Stokes_title", "Al Stokes_header_cell_0_7_0", "Al Stokes_header_cell_0_5_0", "Al Stokes_header_cell_0_4_0", "Al Stokes_header_cell_0_3_0"], "Al Stokes_cell_0_8_1": ["Al Stokes_title", "Al Stokes_header_cell_0_8_0", "Al Stokes_header_cell_0_5_0", "Al Stokes_header_cell_0_4_0", "Al Stokes_header_cell_0_3_0"]}}], "id": 9727, "claim": "Al Stokes had more home runs than than runs batted in.", "label": "REFUTES", "annotator_operations": [{"operation": "start", "value": "start", "time": "0"}, {"operation": "Now on", "value": "undefined", "time": "0.001"}, {"operation": "search", "value": "Al Stokes", "time": "0.022"}, {"operation": "Now on", "value": "Al Stokes", "time": "0.023"}, {"operation": "Highlighting", "value": "Al Stokes_cell_0_7_1", "time": "0.03"}, {"operation": "Highlighting", "value": "Al Stokes_cell_0_8_1", "time": "0.031"}, {"operation": "finish", "value": "finish", "time": "0.054"}, {"operation": "Now on", "value": "Al Stokes", "time": "1619138938.376"}, {"operation": "finish", "value": "finish", "time": "1619138942.255"}], "predicted_evidence": ["Aubrey Huff_sentence_36", "Al Stokes_sentence_1", "Aubrey Huff_sentence_89", "Al Stokes_sentence_3", "Aubrey Huff_sentence_6", "Al Stokes_header_cell_0_0_0", "Al Stokes_header_cell_0_0_0", "Al Stokes_cell_0_1_0", "Al Stokes_cell_0_1_0", "Al Stokes_cell_0_2_0", "Al Stokes_cell_0_2_1", "Al Stokes_cell_0_7_1", "Al Stokes_header_cell_0_8_0", "Al Stokes_cell_0_8_1"], "predicted_label": "REFUTES"}

# Note: {"label": "REFUTES"} and {"predicted_label": "REFUTES"} are aligned. Nice job.
```

## Evaluation

To evaluate your generated predictions locally, simply run the file `evaluate.py` as shown in `eval.sh`:

```bash
python src/feverous/evaluation/evaluate.py --input_path feverous/output/{}.jsonl
 ```

Simply add after `<--input_path>` the postprocessed prediction directory.

```terminal
# eval demo
Feverous scores...
Strict score:  0.19505703422053233
Label Accuracy:  0.5868187579214195
Retrieval Precision:  0.11807112528047603
Retrieval Recall:  0.2932826362484157
Retrieval F1:  0.1683621939343459
```