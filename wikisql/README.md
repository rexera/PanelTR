# WikiSQL in PanelTR

## Flashback

[Seq2SQL: Generating Structured Queries from Natural Language using Reinforcement Learning](http://arxiv.org/abs/1709.00103)

## Main Focus Here

Translating Natural Language into SQL queries.

Specific format requirements are given in our prompts actually, or you can refer to [WikiSQL repo](https://github.com/salesforce/WikiSQL).

## Original Data

Download `data.tar.bz2` from [here](https://github.com/salesforce/WikiSQL/blob/master/data.tar.bz2), then extract it:

```bash
tar xvjf data.tar.bz2
```

They'll all be in the `data` directory.

- `.db`: "original original" data. just ignore them.
- `.jsonl`: instances w/ ground truth, but w/o actual table info.
- `.tables.jsonl`: tables w/ actual content.

> Then make sure you put `dev.jsonl` and `test.jsonl` through `add_index.py` and get `dev_w_index.jsonl` and `test_w_index.jsonl`. You can't afford the hard toil of manual alignment.

For data being directly fed into models, we do some basic processing (i.e. finding and extracting) in the inference script.

## Inference & Postprocessing

```
openai_infer.py  # vanilla
openai_infer_parallel.py # vanilla parallel
openai_infer_single_parallel.py # single-agent parallel
openai_infer_mas_parallel.py # multi-agent parallel
```

You'll get one `.txt` file after this where each line resembles:

```text
index: 0, {"query": {"sel": 2, "agg": 0, "conds": [[0, 0, "terrence ross"]]}}
```

You should note that added indices here are for better breakpoint control.

Next, feed this into `output/postprocess.py` to keep only the query for evaluation.

> Due to the impredictability of model output, discretion and tailored process are advised.
> 
> e.g. 
> - refusal to use index. Please replace `"="` or `'='` to `0` manually.
> - too many info: Try compressing excessive info into one str.
> - ...

## Evaluation

Refer to the official `README.md` for a more detailed version. It's pretty clear.

Or you can also refer to `eval.sh` written by me. haha.

```terminal
# eval demo
100%|███████████████████████████████████| 15878/15878 [00:15<00:00, 996.98it/s]
{
  "ex_accuracy": 0.7850484947726414,
  "lf_accuracy": 0.6887517319561658
}
```