# Progress Handoff

Last updated: 2026-08-10 night.

## Current Working Pattern

We are using the Colab/git/Codex loop documented in `COLAB_WORKFLOW.md`:

1. Run labeled notebook cells in Colab.
2. Save notebook/output state.
3. Sync through git.
4. Codex inspects local notebook outputs and checkpoint files.
5. Codex patches notebook/code/writeups.
6. Codex runs static checks, commits, pushes, and reports the commit hash.

For major edits, run:

```bash
python3 tools/static_notebook_check.py
python3 -m json.tool Panini_Course_Project.ipynb >/tmp/panini_notebook_json_check.json
git diff --check
```

## Completed So Far

### Notebook Usability

- Added a Run Map near the top of `Panini_Course_Project.ipynb`.
- Added visible labels to runnable cells, such as:
  - `FOUNDATION 1: Run Controls`
  - `FOUNDATION 2: Colab/Repo Setup And Paths`
  - `FOUNDATION 3: Shared Checkpoint Helpers`
  - `FOUNDATION 4: Imports And CoursePackage Loading`
  - `Q4A: Parser And Dependency Validation`
  - `Q4B / STAGE A: GPU Decomposition Run`
- Fixed the `STATUS` helper so it can run before setup imports.
- Added `tools/static_notebook_check.py`.
- Added `COLAB_WORKFLOW.md`.

### Q1-Q3

Q1-Q3 have been run in Colab and saved notebook outputs were pulled locally.

Inserted written response drafts for:

- Q1 package audit
- Q2 GSW graph/reconciliation
- Q3 network analysis

Observed Q1 outputs:

- 2Wiki: 100 questions, 765 documents/GSWs, 6,805 entities, 8,887 QA records.
- MuSiQue: 100 questions, 841 documents/GSWs, 8,260 entities, 9,991 QA records.
- Stable `entity_uid` and `qa_uid` checks passed.
- Embedding/index ID-set checks passed.
- Held-out leakage checks passed.

Observed Q2/Q3 outputs:

- 2Wiki native graph: 11,051 nodes, 9,733 edges.
- 2Wiki unreconciled projection: 6,805 nodes, 6,436 edges.
- 2Wiki exact-surface projection: 5,438 nodes, 6,333 edges.
- 2Wiki conservative projection: 6,054 nodes, 6,372 edges.
- MuSiQue native graph: 13,056 nodes, 11,123 edges.
- MuSiQue unreconciled projection: 8,260 nodes, 8,931 edges.
- MuSiQue exact-surface projection: 6,736 nodes, 8,780 edges.
- MuSiQue conservative projection: 7,770 nodes, 8,840 edges.

Important caveat: Q1-Q3 written responses are good drafts but may still need assignment-specific manual items filled in, especially schema examples, pytest summary, and manual reconciliation audit labels/examples.

## Current State Tonight

The user started `Q4B / STAGE A: GPU Decomposition Run` in Colab with:

```python
QUESTION_LIMIT = 2
RUN_DECOMPOSITION_STAGE = True
RUN_RERANK_AND_RICR_STAGE = False
RUN_ANSWER_STAGE = False
RUN_ABLATIONS = False
```

The screenshot showed the Qwen decomposer model downloading from Hugging Face. That is expected. The warning about unauthenticated Hugging Face requests is not fatal; it only means downloads may be slower or rate-limited.

Do not assume Q4B is complete until the Colab cell finishes and the JSONL checkpoints exist.

## What To Continue Next

### Step 1: Finish The Q4B Smoke Test

Let the current `Q4B / STAGE A` run finish if the Colab runtime is still alive.

After it finishes, verify checkpoint files:

```python
print(WORK_ROOT / "cache/2wiki/decompositions.jsonl")
print(WORK_ROOT / "cache/musique/decompositions.jsonl")
```

Inspect the first records:

```python
read_jsonl(WORK_ROOT / "cache/2wiki/decompositions.jsonl")[:2]
read_jsonl(WORK_ROOT / "cache/musique/decompositions.jsonl")[:2]
```

Confirm each record has sensible fields such as:

- `dataset`
- `question_id`
- `question`
- `raw_response`
- `predicted_decomposition`
- `decomposition_valid`
- `validation_errors`
- `dependency_edges`

If the two-question smoke test fails, save/pull the notebook and traceback, then ask Codex to inspect.

### Step 2: Run Full Q4B

If the two-question run succeeds, change `FOUNDATION 1: Run Controls` to:

```python
QUESTION_LIMIT = None

RUN_DECOMPOSITION_STAGE = True
RUN_RERANK_AND_RICR_STAGE = False
RUN_ANSWER_STAGE = False
RUN_ABLATIONS = False
```

If the runtime has not reset, rerun:

1. `FOUNDATION 1: Run Controls`
2. `Q4B / STAGE A: GPU Decomposition Run`

If the runtime has reset, rerun:

1. `FOUNDATION 1: Run Controls`
2. `FOUNDATION 2: Colab/Repo Setup And Paths`
3. `FOUNDATION 3: Shared Checkpoint Helpers`
4. `FOUNDATION 4: Imports And CoursePackage Loading`
5. `Q4A: Parser And Dependency Validation`
6. `Q4B / STAGE A: GPU Decomposition Run`

Q4B is restartable. It reads completed question IDs from the output JSONL, so earlier successful records should be skipped as long as `WORK_ROOT` still points to the same checkpoint location.

### Step 3: Save/Pull For Codex Review

After full Q4B finishes:

1. Save the notebook.
2. Make sure decomposition JSONL files are preserved.
3. Pull/sync locally.
4. Ask Codex to inspect Q4 outputs and write the Q4 response cell.

If `WORK_ROOT` is under `/content`, download or commit important files before the runtime disconnects. If it is under Google Drive, files persist there.

## Next Questions After Q4

### Q5-Q6 Retrieval

Runtime: CPU should be enough.

Run:

1. `FOUNDATION 1`
2. `FOUNDATION 2`
3. `FOUNDATION 3`
4. `FOUNDATION 4`
5. `Q5: Sparse Retrieval Baselines`
6. `Q6: Dense, Hybrid, And Dual Retrieval`

No Qwen model should be loaded for Q5-Q6.

### Q7-Q8 Reranker And RICR

Runtime: GPU, T4 first.

Run after Q5-Q6 have succeeded:

1. Foundation cells
2. `Q4A`
3. `Q5`
4. `Q6`
5. `Q7: Reranker Helpers And Scoring`
6. `Q8A: RICR Tests And Toy Trace`
7. `Q8B / STAGE B: GPU Rerank + RICR Run`

Set only:

```python
RUN_RERANK_AND_RICR_STAGE = True
```

Keep other expensive flags false.

### Q10 Answer Generation

Runtime: GPU.

Run only after RICR traces exist.

Set only:

```python
RUN_ANSWER_STAGE = True
```

Keep decomposition/reranker/ablation flags false.

## Important Operating Rules

- Use CPU for Q1-Q3 and Q5-Q6 where possible.
- Use GPU only for Qwen model stages.
- Keep only one expensive stage flag true at a time.
- Do not keep multiple Qwen models resident in GPU memory.
- Save JSONL checkpoints before switching stages.
- Use `STATUS` to confirm flags/runtime/storage.
- For first attempts, use `QUESTION_LIMIT = 2`.
- For final required runs, use `QUESTION_LIMIT = None`.

