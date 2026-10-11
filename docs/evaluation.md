# Evaluation Framework

## RAG & Quality Metrics
CodePilot AI includes an evaluation pipeline (`EvaluationEngine`) to quantitatively validate retrieval precision, recall, and answer groundedness.

### Metrics Tracked
- **Context Precision**: Ratio of retrieved chunks that are actually relevant to the ground truth standard.
- **Context Recall**: Ratio of relevant standard chunks retrieved by the RAG pipeline.
- **Citation Accuracy**: Proportion of generated code citations (`file:line`) that resolve to valid source lines.
- **Answer Groundedness**: Verification that claims made in the answer are supported by retrieved context.
- **Latency & Token Cost**: End-to-end processing time and token expenditure per query.

### Benchmark Dataset
The evaluation dataset contains benchmark questions for repository structure, authentication flow, duplicate order bug analysis, payment service integration, and pagination design.
