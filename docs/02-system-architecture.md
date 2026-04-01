# 02 - System Architecture

## Pipeline
1. Query intake
2. Input normalization
3. Intent and question-type routing
4. Multi-source retrieval and trend signal update
5. Science-trend reasoning orchestration
6. Safety/compliance gate
7. Structured answer output
8. Logging and error backflow

## Logical layers
- Interaction layer: QA interface
- Application layer: orchestration, recommendation, explanation
- Data/knowledge layer: products, ingredients, trends, feedback, compliance
- Learning layer: distillation flywheel and replay-based regression

## Trend-science conflict rule
- hard constraint: science and safety
- soft optimization: trend relevance
- if conflict occurs: output conservative recommendation + explicit risk note

## Runtime answer states
- direct answer: enough evidence and no blocking safety issue
- clarification: required user information is missing
- conservative answer: evidence is partial or trend-science conflict exists
- refusal/constraint: request crosses compliance or safety boundary

## Runtime outputs (required fields)
- recommendation
- scientific basis
- trend basis
- safety warning
- missing-info note (when needed)
- disclaimer
- cited evidence ids
