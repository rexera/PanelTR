# PanelTR: Zero-Shot Table Reasoning Framework Through Multi-Agent Scientific Discussion

[![arXiv](https://img.shields.io/badge/arXiv-2508.06110-b31b1b.svg)](https://arxiv.org/abs/2508.06110)

PanelTR is a powerful framework for zero-shot table reasoning using Large Language Model (LLM) agents that mimics scientific methodology. It leverages multi-agent collaboration through structured scientific discussion involving Investigation, Self-Review, and Peer-Review processes.

## 🌟 Key Features

- **Zero-Shot Learning**: No training data or task-specific adaptations required
- **Scientific Methodology**: Structured approach with Investigation, Self-Review, and Peer-Review
- **Multi-Agent Collaboration**: Five distinguished scientist personas (Einstein, Newton, Curie, Turing, Tesla)
- **Unified Framework**: Handles multiple table reasoning tasks including QA, fact verification, and SQL generation
- **Robust Reasoning**: Achieves competitive performance through systematic scientific inquiry

## 🔬 Framework Overview

PanelTR operates through three core stages:

1. **Investigation**: Each scientist agent analyzes the problem complexity and formulates initial solutions
2. **Self-Review**: Individual agents validate their solutions through iterative refinement
3. **Peer-Review**: Collaborative discussion among scientist agents to reach consensus or majority voting

### Scientist Personas

- **Albert Einstein**: Explores alternative interpretations and conceptual frameworks
- **Isaac Newton**: Verifies numerical relationships and logical consistency  
- **Marie Curie**: Validates with experimental evidence and practical tests
- **Alan Turing**: Analyzes problem structure and optimizes solution efficiency
- **Nikola Tesla**: Synthesizes diverse perspectives into coherent solutions

## 🚀 Quick Start

### Installation

1. Create and activate conda environment:
```bash
conda create -n paneltr python=3.10
conda activate paneltr
```

2. Install dependencies:
```bash
cd paneltr
pip install -r requirements.txt
python -m spacy download en-core-web-sm
cd paneltr/feverous && python3 -m pip install -e .
```

## Configuration

You need to set your API key in the `.env` file. The framework supports various LLM backends including OpenAI and DeepSeek. You can customize `client`, `MODEL`, `REFLECTION_TURNS`, and `TEMPERATURE` in `paneltr_module/config/paneltr_global_config.py`.

## 📊 Supported Tasks & Benchmarks

The framework has been evaluated on four representative benchmarks:

- **TAT-QA**: Financial question answering with hybrid evidence
- **FEVEROUS**: Fact verification using Wikipedia tables and text
- **WikiSQL**: Natural language to SQL query generation
- **SEM-TAB-FACTS**: Scientific table fact verification

For detailed usage instructions and examples, please refer to the README in each task's directory:

- WikiSQL: See [wikisql/README.md](wikisql/README.md)
- TAT-QA: See [tat-qa/README.md](tat-qa/README.md)
- FEVEROUS: See [feverous/README.md](feverous/README.md)
- SEM-TAB-FACTS: See [sem-tab-facts/README.md](sem-tab-fact/README.md)

## 🎯 Performance

PanelTR demonstrates competitive performance across all benchmarks:
- Outperforms vanilla LLMs and rivals fully supervised models
- Achieves significant improvements on TAT-QA and SEM-TAB-FACTS
- Shows strong zero-shot transferability without task-specific training

## 📚 Citation

If you use PanelTR in your research, please cite our work:

```bibtex
@misc{ma2025paneltr,
      title={PanelTR: Zero-Shot Table Reasoning Framework Through Multi-Agent Scientific Discussion}, 
      author={Yiran Rex Ma},
      year={2025},
      eprint={2508.06110},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2508.06110}, 
}
```

## 📄 Contact

For any questions or feedback, please feel free to open an issue or contact me at mayiran@bupt.edu.cn.
