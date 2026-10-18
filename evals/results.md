**Scorer under test:** mock (offline heuristic)

| Split | Questions | Answers | Strict order (good > mediocre > bad) | Pairwise correct | Ties | Spearman ρ vs. label | Word-count baseline pairwise |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| dev | 6 | 18 | 6/6 | 18/18 | 0 | +0.93 | 17/18 |
| held-out | 4 | 12 | 3/4 | 11/12 | 0 | +0.91 | 10/12 |
| **all** | 10 | 30 | 9/10 | 29/30 | 0 | +0.91 | 27/30 |

| Tier | Mean overall (1-5) | correctness | depth | clarity | structure | relevance |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| good | 4.24 | 5.00 | 3.20 | 5.00 | 3.30 | 4.70 |
| mediocre | 2.96 | 2.80 | 1.80 | 4.50 | 2.80 | 2.90 |
| bad | 2.26 | 1.70 | 1.60 | 4.40 | 1.80 | 1.80 |

| Adversarial (keyword-stuffed, no real explanation) | Overall | Rank among that item's 4 answers (1 = best) |
|---|:-:|:-:|
| rag-technical / keyword_stuffed | 2.60 | 3 |
| sql-technical / keyword_stuffed | 2.40 | 3 |
| prompt-injection-technical / keyword_stuffed | 2.40 | 4 |

### Every scored answer

| Item | Split | Tier | Words | Overall |
|---|---|---|:-:|:-:|
| rag-technical | dev | good | 99 | 4.20 |
| rag-technical | dev | mediocre | 70 | 3.60 |
| rag-technical | dev | bad | 25 | 2.20 |
| sql-technical | dev | good | 64 | 4.40 |
| sql-technical | dev | mediocre | 85 | 2.80 |
| sql-technical | dev | bad | 32 | 2.20 |
| docker-technical | dev | good | 78 | 3.80 |
| docker-technical | dev | mediocre | 38 | 2.80 |
| docker-technical | dev | bad | 36 | 2.60 |
| conflict-behavioral | dev | good | 117 | 4.80 |
| conflict-behavioral | dev | mediocre | 77 | 3.20 |
| conflict-behavioral | dev | bad | 25 | 2.60 |
| promptshield-project | dev | good | 109 | 4.60 |
| promptshield-project | dev | mediocre | 41 | 2.80 |
| promptshield-project | dev | bad | 17 | 2.20 |
| prompt-injection-technical | dev | good | 96 | 4.20 |
| prompt-injection-technical | dev | mediocre | 66 | 3.20 |
| prompt-injection-technical | dev | bad | 28 | 2.80 |
| llm-hallucination-technical | heldout | good | 74 | 3.80 |
| llm-hallucination-technical | heldout | mediocre | 85 | 2.80 |
| llm-hallucination-technical | heldout | bad | 16 | 1.80 |
| rest-api-technical | heldout | good | 71 | 3.80 |
| rest-api-technical | heldout | mediocre | 25 | 2.20 |
| rest-api-technical | heldout | bad | 27 | 2.40 |
| failure-behavioral | heldout | good | 97 | 4.40 |
| failure-behavioral | heldout | mediocre | 61 | 3.00 |
| failure-behavioral | heldout | bad | 13 | 2.20 |
| modelrouter-project | heldout | good | 103 | 4.40 |
| modelrouter-project | heldout | mediocre | 86 | 3.20 |
| modelrouter-project | heldout | bad | 15 | 1.60 |
