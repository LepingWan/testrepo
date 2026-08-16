# PANINI Final Project Summary - 08/16/2026

This document summarizes the completed PANINI/RICR final project, including the workflow we used, major outputs, barriers encountered, fixes applied, and lessons learned. It is intended as a handoff document for teammates reviewing or reproducing the final submission.

## Final Status

The full project pipeline has been run and validated. The notebook contains completed implementations, saved outputs, scoring tables, written responses for Questions 7-12, and submission materialization/validation results.

Completed major milestones:

- Q1-Q3: package audit, graph construction/reconciliation, and network analysis completed.
- Q4B: decomposition completed for both datasets.
- Q5-Q6: sparse, dense, hybrid, and dual retrieval analysis completed.
- Q7: reranker helper implementation completed and written response updated.
- Q8A/Q8B: RICR implementation tested and default RICR traces completed.
- Q9: all controlled ablations completed on both datasets.
- Q10A/Q10C: answer generation and 2Wiki scoring completed.
- Q11: MuSiQue transfer and hop-scaling analysis completed.
- Q12: submission files materialized and validated.

## Repository And Notebook

Local repository:

```text
/Users/lepingwan/Desktop/EC ENGR 232E/testrepo
```

Main notebook:

```text
/Users/lepingwan/Desktop/EC ENGR 232E/testrepo/Panini_Course_Project.ipynb
```

Student RICR implementation:

```text
/Users/lepingwan/Desktop/EC ENGR 232E/testrepo/student_code/ricr.py
```

Workflow notes:

```text
/Users/lepingwan/Desktop/EC ENGR 232E/testrepo/COLAB_WORKFLOW.md
```

Colab/Drive sync helper:

```text
/Users/lepingwan/Desktop/EC ENGR 232E/testrepo/tools/sync_colab_work.py
```

## Durable Colab Output Location

Long-running Colab outputs are stored in Google Drive, not in disposable `/content` storage:

```text
/content/drive/MyDrive/panini-course-project-work
```

Important subdirectories:

```text
/content/drive/MyDrive/panini-course-project-work/cache/2wiki
/content/drive/MyDrive/panini-course-project-work/cache/musique
/content/drive/MyDrive/panini-course-project-work/submission
/content/drive/MyDrive/panini-course-project-work/figures
```

## High-Level Pipeline

The completed system is a staged multi-hop retrieval and answering pipeline:

1. Audit package manifests, IDs, embeddings, and held-out leakage constraints.
2. Build and reconcile graph-structured working memory entities.
3. Analyze graph topology and centrality.
4. Decompose complex questions into structured dependency plans.
5. Retrieve candidate QA evidence with sparse, dense, hybrid, and dual methods.
6. Rerank candidate QA evidence with Qwen.
7. Execute RICR over each decomposition DAG, carrying beams of possible answer chains.
8. Deduplicate final QA evidence from surviving chains.
9. Generate final answers from QA evidence only.
10. Score development outputs and materialize held-out predictions.

The key algorithmic idea is that RICR does not treat decomposed subquestions as unrelated linear searches. It executes a dependency DAG. When a child node depends on multiple parents, RICR combines parent candidate answers before issuing the child query, so later retrieval is conditioned on the joint parent state.

## Final Output Files

### Decompositions

```text
/content/drive/MyDrive/panini-course-project-work/cache/2wiki/decompositions.jsonl
/content/drive/MyDrive/panini-course-project-work/cache/musique/decompositions.jsonl
```

Final status:

```text
2wiki:   100 rows, 100 valid
musique: 100 rows, 100 valid
```

### RICR Traces

```text
/content/drive/MyDrive/panini-course-project-work/cache/2wiki/ricr_traces.jsonl
/content/drive/MyDrive/panini-course-project-work/cache/musique/ricr_traces.jsonl
```

The default Q8B traces completed for both datasets:

```text
2wiki:   100/100 default traces, 0 errors
musique: 100/100 default traces, 0 errors
```

Q9 ablation rows are stored in the same files and distinguished by the `configuration` field, for example `default`, `beam_1`, `bm25`, `dense`, and `rrf`.

### Answers

```text
/content/drive/MyDrive/panini-course-project-work/cache/2wiki/answers.jsonl
/content/drive/MyDrive/panini-course-project-work/cache/musique/answers.jsonl
```

Final status:

```text
2wiki:   100/100 answers, 0 errors
musique: 100/100 answers, 0 errors
```

### Submission Files

Q12A materialized and validated the final required files:

```text
/content/drive/MyDrive/panini-course-project-work/submission/results/2wiki_dev.jsonl
/content/drive/MyDrive/panini-course-project-work/submission/predictions/2wiki_heldout.jsonl
/content/drive/MyDrive/panini-course-project-work/submission/results/musique_dev.jsonl
/content/drive/MyDrive/panini-course-project-work/submission/predictions/musique_heldout.jsonl
```

Validation output:

```text
All required submission files validated.
```

### Reproducibility Files

Q12B writes:

```text
/content/drive/MyDrive/panini-course-project-work/environment.json
/content/drive/MyDrive/panini-course-project-work/environment.txt
/content/drive/MyDrive/panini-course-project-work/RUNME.md
```

## Key Final Metrics

### Q8A RICR Toy Check

```text
RICR toy smoke check passed.
hand-calculated score: 0.8810868114910337
RICR chain score:     0.8810868114910337
```

### Q9 Ablations

All Q9 configurations completed on 20-question slices for both datasets.

Key conclusions:

- Every displayed configuration reached `chain_recovery_rate = 1.0` on both datasets.
- Differences were mainly in latency, evidence size, and strict answer-recovery proxy accuracy.
- On 2Wiki, BM25/dense/RRF were much faster than the default while preserving complete-chain recovery.
- On MuSiQue, `beam_1` and `beam_3` were faster, but `beam_1` produced a very small evidence set.
- RRF or dense are the most defensible robust choices; `beam_3` is a reasonable low-cost option when runtime matters.

Representative Q9 final table rows:

```text
2wiki default: chain_recovery=1.0, answer_accuracy=0.00, evidence=7.05, seconds=414.6
2wiki bm25:   chain_recovery=1.0, answer_accuracy=0.10, evidence=7.05, seconds=241.9
2wiki dense:  chain_recovery=1.0, answer_accuracy=0.05, evidence=6.95, seconds=238.6
2wiki rrf:    chain_recovery=1.0, answer_accuracy=0.05, evidence=6.55, seconds=236.4
musique rrf:  chain_recovery=1.0, answer_accuracy=0.15, evidence=5.40, seconds=211.2
```

### Q10 2Wiki End-To-End Scoring

Overall 2Wiki development metrics:

```text
questions:                80
decomposition_valid_rate: 1.0
chain_recovery_rate:      0.8375
mean_evidence_size:       6.0
mean_supporting_recall:   0.54375
exact_match:              0.4125
token_f1:                 0.4601
mean_retrieval_seconds:   323.8
mean_answer_seconds:      10.7
```

Interpretation: decomposition validity was perfect on the evaluated 2Wiki development set, but final answer accuracy was much lower. This points to retrieval coverage, pruning/substitution errors, and answer synthesis as the main bottlenecks.

### Q11 MuSiQue Transfer And Scaling

MuSiQue results by hop count:

```text
2-hop: 40 questions, supporting recall 0.750, chain recovery 0.975, EM 0.300, F1 0.394
3-hop: 24 questions, supporting recall 0.597, chain recovery 0.958, EM 0.292, F1 0.292
4-hop: 16 questions, supporting recall 0.609, chain recovery 1.000, EM 0.125, F1 0.214
```

Interpretation: complete-chain recovery stayed high, while answer F1 decreased as hop count increased. This suggests that answer synthesis becomes harder as the number of intermediate facts grows, even when retrieval often recovers a chain.

## Barriers Encountered And Fixes

### Google Drive Mount Failures

Early Colab runs failed with Drive credential propagation errors. The workaround was to explicitly control Drive mounting and then use Drive-backed storage for expensive stages.

Useful command:

```python
from google.colab import drive
drive.mount('/content/drive', force_remount=True)
```

### Runtime Disconnects

Colab disconnects wiped `/content` state and interrupted long GPU runs. We moved persistent work to:

```text
/content/drive/MyDrive/panini-course-project-work
```

The expensive stages write restartable JSONL checkpoints keyed by stable `question_id`, so reruns skip completed rows.

### Model Download/Reconstruction Appearing Stuck

Large Hugging Face downloads sometimes looked frozen during file reconstruction or weight loading. The runs were usually still active. We added verbose prints around model loading, per-question starts, completions, and checkpoint writes.

### Missing RICR Implementation

Q8A initially failed with:

```text
NotImplementedError('Implement PANINI DAG RICR')
```

We implemented RICR in `student_code/ricr.py` and ensured Colab copied that file into the importable package path:

```text
/content/panini-course-project/panini_course/ricr.py
```

### Generated Queries Without Dense Embeddings

Some generated RICR queries did not have supplied dense query embeddings. The retrieval helper now falls back to BM25 for those generated queries rather than failing.

### Q12 Validation Ordering

Q12A initially checked for required files before materializing them. We patched it so the submission files are created first and then validated.

### Q7 Expectations

Q7 is primarily a helper/implementation cell. It usually produces no standalone Stage B output table. It defines reranking functions that Q8B and Q9 later use.

## Colab Execution Lessons

- Use CPU for Q1-Q7, Q10C, Q11, and Q12.
- Use GPU/T4 for Q4B, Q8B, Q9, and Q10A.
- Enable exactly one expensive stage flag at a time.
- Do not keep multiple Qwen models resident simultaneously.
- Use Google Drive-backed `WORK_ROOT` for long-running stages.
- Save notebook outputs back to GitHub after major milestones.
- Pull locally, audit outputs, patch answers/code, run static checks, commit, and push.

## Final Validation Performed Locally

Before this summary was finalized, the notebook passed:

```text
python3 tools/static_notebook_check.py
```

The lightweight student-code tests also passed in previous final-answer cleanup passes:

```text
direct student_code tests passed: 8
```

The written-response audit showed no remaining placeholder text in Questions 7-12 after the Q8 cleanup.

## Remaining Caution Before Submission

The notebook still contains some control/helper cells marked as "Remove before submission". These were intentionally left in place during development because they make the notebook easier to rerun and recover. If the final grading instructions require a cleaner notebook, perform a final cleanup pass to remove or hide those cells only after confirming no one needs to rerun the pipeline.

## Recommended Final Review Split

For a three-person team, the most efficient final review is ownership-based rather than everyone reviewing everything:

- Reviewer 1: notebook execution/state and required output files.
- Reviewer 2: written responses and metric interpretation.
- Reviewer 3: code correctness, RICR implementation, and reproducibility files.

Each reviewer should report concrete findings rather than general approval. The highest-risk areas are Q8/Q9 reasoning, Q10/Q11 metric interpretation, and Q12 submission-file validation.
