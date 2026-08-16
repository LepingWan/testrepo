# Colab Workflow

This repo uses a Colab-first execution loop with local Codex review.

## Sync Loop

1. Run the relevant labeled cells in Colab.
2. Save the notebook and any generated outputs.
3. Sync through git:
   - In Colab, pull before continuing: `!git pull`
   - After local Codex edits are pushed, pull again in Colab.
4. Locally, Codex inspects the pulled notebook outputs, checkpoint files, and exports.
5. Codex updates notebook text/code as needed.
6. For major edits, Codex runs static dry-run checks, commits, pushes, and reports the commit hash.

## Versioned Student Code In Colab

Opening `Panini_Course_Project.ipynb` from GitHub in Colab does not automatically
clone the surrounding `testrepo` files into `/content`. The notebook therefore
clones or pulls the lightweight team repo at `https://github.com/LepingWan/testrepo.git`
inside `FOUNDATION 2` when `Path.cwd() / "student_code"` is missing. That clone
is only used as the versioned source for files such as `student_code/ricr.py`
and `student_code/test_student_ricr.py`; the public PANINI package is still
cloned separately from `https://github.com/YigitTurali/panini-course-project.git`.

After Codex pushes changes to `student_code`, rerun `FOUNDATION 2` in Colab so
it copies the committed file into:

- `/content/panini-course-project-work/student_code/ricr.py`
- `/content/panini-course-project/panini_course/ricr.py`

## Notebook Run Order

After every runtime reset, run the foundation cells first:

1. `FOUNDATION 1: Run Controls`
2. `FOUNDATION 2: Colab/Repo Setup And Paths`
3. `FOUNDATION 3: Shared Checkpoint Helpers`
4. `FOUNDATION 4: Imports And CoursePackage Loading`

Then run only the labeled stage needed, using the notebook's Run Map.

For Q8, run `Q8 RUN CONTROL` after `Q8A` and before `Q8B / STAGE B`.
That local control cell flips the stage flags to reranker/RICR mode, keeps
Drive durability enabled, and avoids scrolling back to `FOUNDATION 1`.

## Runtime Policy

Use CPU for:

- Q1 package audit
- Q2 graph construction/reconciliation
- Q3 network analysis
- Q4 parser validation
- Q5 sparse retrieval
- Q6 dense/FAISS retrieval, unless Colab-specific behavior suggests otherwise
- Q10/Q11 scoring tables
- Q12 submission/reproducibility cells

Use GPU for Qwen model stages:

- `Q4B / STAGE A: GPU Decomposition Run`
- `Q8B / STAGE B: GPU Rerank + RICR Run`
- Q9 ablations that use the reranker
- `Q10A: Answer Formatting And GPU Answer Run`

Run exactly one expensive model stage at a time. Do not keep multiple Qwen models resident in GPU memory. After a model stage finishes, save checkpoints, then restart or clear GPU memory before loading the next model.

## Stage Flags

Change stage flags manually in:

`FOUNDATION 1: Run Controls`

For example, for Q4 decomposition:

```python
RUN_DECOMPOSITION_STAGE = True
RUN_RERANK_AND_RICR_STAGE = False
RUN_ANSWER_STAGE = False
RUN_ABLATIONS = False
QUESTION_LIMIT = 2
```

Keep `QUESTION_LIMIT = 2` for smoke tests. Increase gradually before setting `QUESTION_LIMIT = None` for required final runs.

## Outputs And Checkpoints

Prefer structured output files over relying only on visible notebook output.

Important locations:

- `WORK_ROOT / "exports"` for CSV/JSON tables used in written answers
- `WORK_ROOT / "figures"` for plots
- `WORK_ROOT / "cache" / <dataset> / "decompositions.jsonl"`
- `WORK_ROOT / "cache" / <dataset> / "ricr_traces.jsonl"`
- `WORK_ROOT / "cache" / <dataset> / "answers.jsonl"`
- `WORK_ROOT / "submission"` for final deliverables

For long Colab runs, keep `MOUNT_DRIVE_IN_COLAB = True` and
`REQUIRE_DURABLE_WORK_ROOT = True` in `FOUNDATION 1`. Then `FOUNDATION 2`
mounts Google Drive and sets `WORK_ROOT` to:

`/content/drive/MyDrive/panini-course-project-work`

If Drive authorization fails, the notebook stops before expensive stages write
wipeable checkpoints. For a disposable smoke run only, you can temporarily set
`REQUIRE_DURABLE_WORK_ROOT = False`; if `WORK_ROOT` is under `/content`,
download or commit important files before the runtime disconnects.

## Sync Drive Work Outputs Into Git

The Colab Drive path `/content/drive/MyDrive/panini-course-project-work` exists
only inside Colab. To snapshot those durable outputs into this repo, run from an
authenticated `testrepo` clone in Colab after Drive is mounted:

```bash
python tools/sync_colab_work.py \
  --source /content/drive/MyDrive/panini-course-project-work \
  --dest panini-course-project-work \
  --commit --push
```

For an in-progress long run, it is safe to sync periodically. JSONL files are
copied defensively: if a file is being appended at the exact moment of sync, the
destination snapshot drops an incomplete trailing JSONL row while leaving the
Drive source untouched.

Before committing very large outputs, check the script warnings. GitHub rejects
individual files above 100 MB.

## Dynamic RICR Queries

The supplied dense query embeddings only cover fixed public benchmark queries.
RICR creates new subqueries after entity substitution, so those generated
queries may not exist in `QueryEmbeddingStore`. The notebook's Q7 reranking
helper therefore uses the requested dense/dual backend when an embedding exists
and falls back to BM25 for generated queries without supplied embeddings.

`Q8B / STAGE B` should print one heartbeat per dataset and question. If the
only visible output is model loading, it is still before the RICR loop; once
RICR starts, look for `Q8B: RICR start`, `Q8B: RICR done`, or `Q8B: RICR failed`.
Q8B also requires `decompositions.jsonl` from Q4B in `WORK_ROOT / "cache"`.
If those files are missing, run Q4B first.

## Static Dry Run Before Commits

For major notebook edits, run:

```bash
python3 tools/static_notebook_check.py
python3 -m json.tool Panini_Course_Project.ipynb >/tmp/panini_notebook_json_check.json
git diff --check
```

The checker verifies notebook JSON, code-cell syntax, run-map labels, the `STATUS` helper, and that saved notebook outputs were not accidentally wiped.

## Codex Commit Habit

For major edits, Codex should:

1. Make the edit.
2. Run static dry-run checks.
3. Commit with a clear message.
4. Push to `main`.
5. Report the commit hash and next Colab action.
