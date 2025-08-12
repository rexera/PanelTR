# SEM-TAB-FACTS (Semeval 2021, Task 9), in PanelTR

## Flashback
SemEval-2021 Task 9 (Statement Verification and Evidence Finding with Tables).

Competition webpage: https://sites.google.com/view/sem-tab-facts

Original paper: [Volta at SemEval-2021 Task 9: Statement Verification and Evidence Finding with Tables using TAPAS and Transfer Learning](https://aclanthology.org/2021.semeval-1.180/).

## Our Focus

**Task A: Fact Verification.**

Given a statement (`text`) and relevant tabular info, predict whether the statement is entailed / refuted / unknown.

## Original Data

**dev**:

Download dev set data from [here](https://drive.google.com/file/d/1I1E0rl234a7m9XqVbXJR6UwJ9gbPYcii/view) and put it in `data/dev/`.

`data/dev/input`: Pure Instances

`data/dev/output`: Instances w/ Ground Truth

---

**test**:

Download test set **input** data from [here](https://drive.google.com/file/d/12z4nvD_dE85SKydkCUrI6jtcwwGnqdPs/view) and save it as `data/test/input`;

Download test set **output** data from [here](https://drive.google.com/file/d/1Trfq0Zd2tcAV4JIR9puopmy6NC1lMj5S/view) and save it as `data/test/output`.

`data/input`: Pure Instances

`data/output`: Instances w/ Ground Truth

## Preprocessing

```text
data/preprocess.py
```

This script transform `.xml`files to one single `.jsonl` file for the sake of maximal information density.

Preprocessed data are like:
```text
data/dev_openai.jsonl
data/test_openai.jsonl
```

```json
# data demo
{"global_id": 0, "xml_id": "10282", "table_id": "Table 1", "id": "0", "text": "(PCuN) vs. (PCuN) c has the value 124.4 under M2 +", "caption": "     Selected distances [Å] and angles [°] of optimized structures of         1        . DFT PBE86/def2TZV gas phase.         a        Relative free Energy differences at room temperature (kcal mol         -1        ).         b        Relative difference of electronic energies (kcal mol         -1        ).         c        Angle between the planes spanned by the P,N-atoms of one ligand and the copper center    ", "legend": "", "footnote": "", "rows": [["", "M1               +", "M2               +"], ["ΔG             a", "+3.6", "0.0"], ["ΔE             b", "+3.5", "0.0"], ["P1-Cu", "2.578", "2.381"], ["P2-Cu", "2.713", "2.379"], ["N1-Cu", "1.948", "1.989"], ["N2-Cu", "1.949", "1.995"], ["P1-Cu-P2", "135.1", "124.1"], ["N1-Cu-N2", "159.8", "113.1"], ["P1-Cu-N1", "81.2", "83.1"], ["P2-Cu-N2", "79.9", "82.9"], ["P2-Cu-N1", "101.8", "134.4"], ["P2-Cu-N2", "112.0", "124.4"], ["(PCuN) vs. (PCuN)             c", "52.8", "79.8"]]}
```

## Inference

```
openai_infer.py  # vanilla
openai_infer_parallel.py # vanilla parallel
openai_infer_single_parallel.py # single-agent parallel
openai_infer_mas_parallel.py # multi-agent parallel
```

```json
# inference demo
{"global_id": 0, "xml_id": "10282", "table_id": "Table 1", "statement_id": "0", "type": "refuted"}
```

## Postprocessing

This unfortunately needs to be dealt with manually. After inference, you'll get a `.jsonl`file. And with `outputs/postprocess_xml.py`, we transform it into a new directory filled with qualified `.xml` files with the same, original file name.

Make sure you set:
- `xml_folder` to the **input** directory. 

(In this way we ignore Task B, you'll see `task_b_f1_total: 0.0000`)

- `json_file` to the model prediction.

## Evaluation

```text
official_evaluation_code/evaluate.py
```

Modify the following variables:

- `output_dir`: Like `sem-tab-fact/eval_results`. Here stores the final scores with a `.txt` file.
- `submit_dir`: This is the **model prediction** directory. Set to `sem-tab-fact/data/output_test_gold/` for a mock evaluation (It should be all 1.000). Make sure model prediction holds the same schema as the `.xml`files in output given by the official.
- `truth_dir` = This is the **ground truth** directory, an example being `sem-tab-fact/data/dev/output`

```terminal
# eval demo
task_a_2way_f1_total: 0.7372 
task_a_3way_f1_total: 0.7176 
task_b_f1_total: 0.0000 
```