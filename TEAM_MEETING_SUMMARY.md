# PANINI Final Project Team Meeting Summary - 8.16.2026

This document summarizes the project work completed so far, the barriers encountered, how we addressed them, where the outputs are stored, and the remaining work before submission.

## Current Status

The integrated PANINI/RICR pipeline is mostly complete. We have run the main decomposition, retrieval/RICR, answer generation, scoring, and submission-materialization stages. The main remaining experimental task is completing or deciding how far to continue Question 9 ablations.

Completed major outputs:

- Q4B decompositions: complete for both datasets.
- Q8B default RICR traces: complete for both datasets.
- Q10A answer generation: complete for both datasets.
- Q10C 2Wiki scoring: complete.
- Q11 MuSiQue transfer/scaling analysis: complete.
- Q12 submission materialization and validation: complete.
- Q9 ablations: in progress.

## High-Level Pipeline

The project implements a staged multi-hop retrieval and answering system:

1. Decompose each complex question into a structured multi-hop plan.
2. Validate the decomposition as a dependency graph/DAG.
3. Retrieve candidate QA evidence for each subquestion.
4. Rerank retrieved candidates with Qwen.
5. Execute RICR over the decomposition DAG, carrying beams of possible answer chains.
6. Deduplicate the final evidence from surviving chains.
7. Generate final answers using the answer model.
8. Score outputs and materialize final submission files.

The key design idea is that RICR does not retrieve each subquestion independently. It carries candidate answers through the dependency graph. When a node depends on multiple parent nodes, RICR combines parent candidate answers and issues a grounded child query.

## Work Completed

### Assignment Analysis And Planning

We reviewed the project handout, PANINI walkthrough, and discussion material to identify the major stages and compute requirements. We learned that Q4B, Q8B, Q9, and Q10A are the expensive model stages because they load Qwen models. CPU-only analysis is suitable for Q1-Q7 setup, Q10C, Q11, and Q12.

### Colab/GitHub Workflow

We established a workflow where the notebook is executed in Google Colab and synchronized back through GitHub. The local project repository is:

```text
/Users/lepingwan/Desktop/EC ENGR 232E/testrepo
```

The main notebook is:

```text
/Users/lepingwan/Desktop/EC ENGR 232E/testrepo/Panini_Course_Project.ipynb
```

The durable Colab work directory is:

```text
/content/drive/MyDrive/panini-course-project-work
```

This Drive-backed directory is important because Colab runtime storage under `/content` can be lost after disconnects.

### RICR Implementation

The initial RICR scaffold raised:

```text
NotImplementedError('Implement PANINI DAG RICR')
```

We implemented RICR in:

```text
student_code/ricr.py
```

The Q8A toy smoke test passed with matching hand-computed and implementation scores:

```text
hand-calculated score: 0.8810868114910337
RICR chain score:     0.8810868114910337
```

### Q4B Decomposition

Q4B generated and validated decompositions for both datasets.

Output files:

```text
/content/drive/MyDrive/panini-course-project-work/cache/2wiki/decompositions.jsonl
/content/drive/MyDrive/panini-course-project-work/cache/musique/decompositions.jsonl
```

Final status:

```text
2wiki:   100 rows, 100 valid
musique: 100 rows, 100 valid
```

### Q8B Default RICR

Q8B executed reranking and RICR over the saved decompositions.

Output files:

```text
/content/drive/MyDrive/panini-course-project-work/cache/2wiki/ricr_traces.jsonl
/content/drive/MyDrive/panini-course-project-work/cache/musique/ricr_traces.jsonl
```

Final default status:

```text
2wiki:   100/100 default traces, 0 errors
musique: 100/100 default traces, 0 errors
```

### Q10A Answer Generation

Q10A generated final answers using the saved RICR traces.

Output files:

```text
/content/drive/MyDrive/panini-course-project-work/cache/2wiki/answers.jsonl
/content/drive/MyDrive/panini-course-project-work/cache/musique/answers.jsonl
```

Final status:

```text
2wiki:   100/100 answers, 0 errors
musique: 100/100 answers, 0 errors
```

### Q10C 2Wiki Scoring

Q10C scored 2Wiki development results.

Overall 2Wiki metrics:

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

Important interpretation: decomposition validity was perfect on the evaluated set, but answer accuracy was much lower. This suggests the main failures are downstream of decomposition: retrieval coverage, later-hop substitution/pruning, and answer synthesis.

### Q11 MuSiQue Transfer And Scaling

Q11 evaluated MuSiQue transfer by hop count.

Results:

```text
2-hop: 40 questions, chain recovery 0.975, EM 0.300, F1 0.394
3-hop: 24 questions, chain recovery 0.958, EM 0.292, F1 0.292
4-hop: 16 questions, chain recovery 1.000, EM 0.125, F1 0.214
```

Interpretation: complete-chain recovery stayed high, but answer F1 dropped as hop count increased. This suggests that answer synthesis over more intermediate facts becomes harder even when retrieval is often successful.

### Q12 Submission Materialization

Q12A was patched so that it actually calls the materialization function before validation. It now creates and validates the required submission JSONL files.

Validated submission files:

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

Q12B writes reproducibility information:

```text
/content/drive/MyDrive/panini-course-project-work/environment.json
/content/drive/MyDrive/panini-course-project-work/environment.txt
/content/drive/MyDrive/panini-course-project-work/RUNME.md
```

## Current Q9 Ablation Status

Q9 writes ablation traces into the same `ricr_traces.jsonl` files used by Q8B. Rows are distinguished by the `configuration` field, for example:

```json
{"configuration": "beam_1"}
{"configuration": "bm25"}
{"configuration": "dense"}
{"configuration": "rrf"}
```

Current Q9 status from the latest logs:

```text
2wiki default:              20/20
2wiki beam_1:               20/20
2wiki beam_3:               20/20
2wiki k_5:                  20/20
2wiki unique_off:           20/20
2wiki last_hop:             20/20
2wiki parent_threshold_off: 20/20
2wiki bm25:                 in progress
2wiki dense:                not started
2wiki rrf:                  not started
musique ablations:          not started
```

Q9 must run on GPU/T4 because it repeatedly calls the Qwen reranker. Running Q9 on CPU is technically possible but too slow to be practical.

## Barriers Encountered And Fixes

### Google Drive Mount Failures

Early Colab runs failed with Drive credential propagation errors. We added logic to control Drive mounting and eventually made durable Drive storage the default for expensive runs.

Useful recovery command:

```python
from google.colab import drive
drive.mount('/content/drive', force_remount=True)
```

### Runtime Disconnects

Colab disconnects caused concern because `/content` is disposable. We moved long-running checkpoints to Google Drive:

```text
/content/drive/MyDrive/panini-course-project-work
```

All major expensive stages write JSONL checkpoints and resume by stable `question_id`.

### Model Downloads Appearing Stuck

Q4B, Q8B, and Q9 model downloads sometimes appeared stuck during Hugging Face reconstruction. This was normal: model shards were being reconstructed locally before loading. We added verbose print statements around model loading and per-question checkpoints.

### Missing RICR Implementation

Q8A originally failed because the runtime still had the scaffold `ricr.py`. We fixed the setup so versioned student code is copied into:

```text
/content/panini-course-project/panini_course/ricr.py
```

### Dense Embedding Missing For Generated Queries

RICR generates new subqueries dynamically. Some generated queries do not have supplied dense embeddings. We added a BM25 fallback for generated queries when dense, dual, or RRF retrieval cannot use supplied embeddings.

### Q10C Missing Imports After Runtime Reset

Q10C originally failed with:

```text
NameError: exact_match is not defined
```

We fixed this by adding local imports inside Q10C.

### Q11 Missing Figure Directory

Q11 originally failed while saving the plot because `figures_dir` was undefined. We added:

```python
figures_dir = WORK_ROOT / 'figures'
figures_dir.mkdir(parents=True, exist_ok=True)
```

### Q12A Did Not Materialize Files

Q12A defined `materialize_submission()` but did not call it. We patched Q12A to call the function before validating files.

### Q9 Accidentally Run On CPU

Q9 was briefly run on CPU, causing extremely slow progress. Lesson: any stage that loads or calls Qwen should run on GPU/T4.

GPU-required stages:

```text
Q4B decomposition
Q8B reranking/RICR
Q9 ablations
Q10A answer generation
```

CPU-safe stages:

```text
Q1-Q7 setup/analysis
Q10C scoring
Q11 analysis
Q12 submission generation/validation
```

## Lessons Learned

- Keep model stages separate; do not keep multiple Qwen models resident simultaneously.
- Use Drive-backed JSONL checkpoints for every expensive stage.
- Checkpoint by stable `question_id` so reconnects can resume cleanly.
- Notebooks should import their own dependencies in each major section because runtime resets clear memory.
- Q9 is deceptively expensive because each ablation row calls the reranker repeatedly.
- Dense retrieval depends on supplied query embeddings; generated RICR queries may need sparse fallback.
- The notebook should be edited by one person at a time to avoid merge conflicts.
- Review should be owned by role, not by everyone reviewing everything.

## Recommended Team Review Split

### Integration Owner

Responsible for:

- finishing Q9 or deciding where to stop,
- saving/pushing final outputs,
- merging changes,
- running final validation,
- final submission package.

### Code/Reproducibility Reviewer

Review:

- `student_code/ricr.py`,
- Q8/Q9 RICR usage,
- checkpoint/resume behavior,
- Q12 submission generation,
- held-out label leakage,
- `RUNME.md` and environment files.

Deliverable:

```text
Must fix:
Nice to fix:
Looks good:
```

### Writing/Results Reviewer

Review:

- Q7-Q12 written responses,
- whether claims match tables and outputs,
- whether wording is appropriate for a graduate-level submission,
- whether Q9 caveat/final numbers are acceptable.

Deliverable:

```text
Q7:
Q8:
Q9:
Q10:
Q11:
Q12:
```

## Remaining Work Before Submission

1. Finish Q9 ablations or decide that the completed subset is sufficient.
2. Save/push Q9 outputs.
3. Replace the provisional Q9 written response with final measured interpretation.
4. Add/polish Q7 written response.
5. Run a final wording polish on Q7-Q12.
6. Clean temporary helper cells marked “Remove before submission” only when ready.
7. Confirm Q12A validation still passes.
8. Confirm final submission files and reproducibility files are included.
9. Run final static checks and commit/push.

## Key File Locations

Main notebook:

```text
/Users/lepingwan/Desktop/EC ENGR 232E/testrepo/Panini_Course_Project.ipynb
```

RICR implementation:

```text
/Users/lepingwan/Desktop/EC ENGR 232E/testrepo/student_code/ricr.py
```

Tests:

```text
/Users/lepingwan/Desktop/EC ENGR 232E/testrepo/student_code/test_student_ricr.py
```

Drive work root:

```text
/content/drive/MyDrive/panini-course-project-work
```

Decomposition checkpoints:

```text
/content/drive/MyDrive/panini-course-project-work/cache/2wiki/decompositions.jsonl
/content/drive/MyDrive/panini-course-project-work/cache/musique/decompositions.jsonl
```

RICR/Q9 traces:

```text
/content/drive/MyDrive/panini-course-project-work/cache/2wiki/ricr_traces.jsonl
/content/drive/MyDrive/panini-course-project-work/cache/musique/ricr_traces.jsonl
```

Answer checkpoints:

```text
/content/drive/MyDrive/panini-course-project-work/cache/2wiki/answers.jsonl
/content/drive/MyDrive/panini-course-project-work/cache/musique/answers.jsonl
```

Final submission files:

```text
/content/drive/MyDrive/panini-course-project-work/submission/results/2wiki_dev.jsonl
/content/drive/MyDrive/panini-course-project-work/submission/predictions/2wiki_heldout.jsonl
/content/drive/MyDrive/panini-course-project-work/submission/results/musique_dev.jsonl
/content/drive/MyDrive/panini-course-project-work/submission/predictions/musique_heldout.jsonl
```

Reproducibility files:

```text
/content/drive/MyDrive/panini-course-project-work/environment.json
/content/drive/MyDrive/panini-course-project-work/environment.txt
/content/drive/MyDrive/panini-course-project-work/RUNME.md
```
