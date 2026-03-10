# 02 - System Architecture

## Pipeline
1. Query intake
2. Input normalization
3. Multi-source retrieval and trend signal update
4. Science-trend reasoning orchestration
5. Safety/compliance gate
6. Structured answer output
7. Logging and error backflow

## Logical layers
- Interaction layer: QA interface
- Application layer: orchestration, recommendation, explanation
- Data/knowledge layer: products, ingredients, trends, feedback, compliance
- Learning layer: distillation flywheel and replay-based regression

## Trend-science conflict rule
- hard constraint: science and safety
- soft optimization: trend relevance
- if conflict occurs: output conservative recommendation + explicit risk note

## Runtime outputs (required fields)
- recommendation
- scientific basis
- trend basis
- safety warning
- disclaimer
