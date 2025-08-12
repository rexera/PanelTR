# TAT-QA, in PanelTR

## Flashback


**TAT-QA** (**T**abular **A**nd **T**extual dataset for **Q**uestion **A**nswering) contains 16,552 questions associated with 2,757 hybrid contexts 
from real-world financial reports. ([TAT-QA dataset](https://github.com/NExTplusplus/TAT-QA/tree/master/dataset_raw); [TAT-QA website](https://nextplusplus.github.io/TAT-QA/); [paper](https://aclanthology.org/2021.acl-long.254.pdf)).

## Main Focus Here

For a given table and some relevant paragraphs, answer a series of questions in the following format:

```json
{
  "question-uid": [
    "answer",
    "scale/unit"
  ]
}
```

For a more detailed schema explanation, please refer to [TAT-QA website](https://nextplusplus.github.io/TAT-QA/).

## Data Needed

Our main focus would be `dataset_raw/tatqa_dataset_dev.json`, which is the original dev set. You can download it from [here](https://github.com/NExTplusplus/TAT-QA/tree/master/dataset_raw).

For a better breakpoint control, we also offered a `_w_index` version that can be generated from `dataset_raw/add_index.py` with a continuous index space for all question.

## Inference

```
openai_infer.py  # vanilla
openai_infer_parallel.py # vanilla parallel
openai_infer_single_parallel.py # single-agent parallel
openai_infer_mas_parallel.py # multi-agent parallel
```

Output would be in `output`directory and resemble:

```json
"eb50d3aa-16da-4087-9ab2-10106ebd10e7": [
        268,
        [
            "4427"
        ],
        "thousands"
    ]
```

You may want to merge all batches using `output/final_merge.py`.

## Evaluation

```text
tatqa_eval.py
```
It goes hand in hand with `tatqa_metric.py`, `tatqa_metric_test.py`, `tatqa_utils.py`, and `tatqa_utils_test.py`.

Please refer to `sample_prediction.json` and adhere strictly to its schema.

Also refer to `eval.sh` for eval instruction demos.