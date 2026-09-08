# IP-SAKTI — CodeAmigos

## Project Goal

Build a working SIH 2026 MVP of IP-SAKTI, an AI-powered IP and
regulatory navigator for Ayurveda and traditional knowledge.

## Primary Objective

Prioritize a demonstrable, working MVP over unnecessary complexity.

The application must allow a user to:
1. Ask an IP/regulatory question.
2. Classify the query/product.
3. Route it toward relevant IP/regulatory information.
4. Retrieve evidence from the project's knowledge base.
5. Generate an evidence-grounded answer.
6. Display citations/evidence.
7. Abstain when sufficient evidence is unavailable.

## Development Rules

- Inspect the existing code before modifying it.
- Do not rewrite working code unnecessarily.
- Do not introduce microservices unless clearly necessary.
- Prefer a simple modular monolith for the MVP.
- Keep frontend and backend clearly separated.
- Keep AI/RAG logic modular.
- Use environment variables for secrets.
- Never hardcode API keys.
- Never fabricate authoritative government data.
- Clearly label mock/demo data.
- Do not claim an external API exists unless verified.
- Every AI-generated factual answer should be traceable to retrieved evidence.
- If evidence is insufficient, the system should say so instead of inventing an answer.
- Run tests after significant implementation changes.
- Fix errors before moving to the next feature.

## MVP Priority

Priority order:

1. Application skeleton
2. Backend API
3. Frontend UI
4. Query flow
5. Document ingestion
6. Retrieval/RAG
7. Evidence and citations
8. Product/query classification
9. IP/regulatory routing
10. Multilingual support
11. Demo polish

## Token/Scope Discipline

Do NOT attempt to implement the entire project in one task.

For every task:
- Inspect only the files relevant to the task.
- Make the smallest coherent change.
- Avoid unnecessary refactoring.
- Run targeted tests.
- Report what changed and what remains.

Do not implement future features unless explicitly requested.