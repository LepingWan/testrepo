# PANINI Submission Readiness Plan - August 23, 2026

Source of truth: `ECE232_S26_Final_Project.pdf`, due Friday, August 28, 2026 at 11:59 PM Pacific Time.

This document records what is currently missing or risky, how to close the gaps, and how to build the final `report.pdf`. The goal is to keep the notebook reproducible while preventing accidental teammate uploads from overwriting working outputs.

## Current State

- Latest notebook: `Panini_Course_Project.ipynb`.
- Current durable Colab work folder: `/content/drive/MyDrive/panini-course-project-work`.
- Local downloaded work folder used for inspection: `/Users/lepingwan/Downloads/panini-course-project-work`.
- GitHub repo output folder exists as `panini-course-project-work/`, but currently only contains a placeholder README. Final outputs still need to be synced into the repo.
- Q1 now includes the required dataset/split count table.
- Q4C now loads `questions/decomposition_validation.jsonl` and reports reviewed metrics.
- Q8 default RICR traces and Q9 ablation traces exist in the Drive work folder.
- Q10/Q11 answer outputs and the four minimal submission JSONL files exist in the Drive work folder.

## Rubric Gaps And Risks

### Critical Before Submission

1. Q7 appears under-run or under-documented.
   - Rubric requires one comparison table for three scoring rules: reranker probability, reciprocal retrieval rank, and 50/50 hybrid.
   - Rubric also requires two annotated retrieval traces: one where reranking improves first relevant rank and one where it worsens it.
   - Current notebook cell `Q7: Reranker Helpers And Scoring` has no saved outputs. The written response is conceptual, but does not clearly cite an observed Q7 comparison table and two observed top-five traces.

2. Q8 prose and hand-worked beam are incomplete relative to the PDF rubric.
   - Current tests in `student_code/test_student_ricr.py` are promising and cover many required RICR behaviors.
   - Current notebook shows the toy smoke score, but the PDF asks for one hand-worked two-parent example with `B=2` and `k=2`, listing parent Cartesian products, harmonic scores, concrete child queries, final expansions, and retained beams.
   - Current written answer explains converging DAGs and beam diversity, but it should also explicitly explain:
     - why intermediate entity grouping and final QA-level selection intentionally differ;
     - why raw document-local IDs would silently corrupt diversity.

3. Q12 submission JSONL schema is currently too minimal.
   - Section 9.2 requires fields such as `dataset`, `split`, `predicted_decomposition`, `decomposition_valid`, `retrieval_backend`, `beam_width`, `candidates_per_hop`, `chains`, `evidence_qa_ids`, `latency_ms`, and `answer_context_tokens`.
   - Current files contain only:
     - development: `question_id`, `question`, `predicted_answer`, `exact_match`, `token_f1`, `answer_seconds`;
     - held-out: `question_id`, `question`, `predicted_answer`, `answer_seconds`.
   - This is the highest risk for Q12 and final handoff, even though row counts currently validate.

4. `report.pdf` does not exist yet.
   - Q12 requires `report.pdf`, organized by Questions 1-12, limited to 18 pages excluding references and a two-page appendix.
   - It also requires a one-page system story following one question from decomposition through retrieval, RICR, and final answer.

5. Final allowed artifacts are not yet synced into GitHub.
   - Required: completed notebook, imported Python modules/tests, four development/held-out JSONL files, `environment.txt`, `RUNME.md`, and `report.pdf`.
   - Do not commit downloaded model weights, provided embeddings, FAISS indices, or dataset copies.

### High Priority Quality Risks

6. Q9 metrics do not fully match the rubric wording.
   - PDF asks for supporting-QA recall, complete-chain recovery, answer EM/F1, mean latency, and mean evidence count.
   - Current table reports chain recovery, an `answer_accuracy` proxy, latency, and evidence count. It may not report answer EM/F1 from the Stage C answerer for each ablation.
   - Keep the existing Q9 run, but final report should label exactly what `answer_accuracy` means. If it is not EM/F1, either compute EM/F1 from available predictions or state the limitation clearly.

7. Q10/Q11 metric tables are narrower than the PDF asks.
   - PDF asks for Recall@1/5/10/15, MRR, supporting-document recall, supporting-QA recall, complete-chain recovery, average surviving chains, average unique current answers, EM/F1, latency, peak GPU memory, reranked-candidate count, evidence count, and answer-context tokens.
   - Current Q10/Q11 tables include decomposition validity, chain recovery, evidence size, supporting recall, EM/F1, and latency, but not all retrieval metrics, token counts, peak GPU memory, average surviving chains, or unique current answers.
   - These can likely be computed from saved `ricr_traces.jsonl` and `answers.jsonl` without rerunning expensive GPU stages.

8. Q5/Q6 output persistence is uncertain.
   - Q5 asks for sparse search code, performance tables, latency, failure examples, and sparse retrieval baselines.
   - Q6 asks for a saved top-15 retrieval trace for every development atomic question and one route-by-route explanation.
   - Notebook tables exist, but it is not yet clear that the required saved top-15 traces are materialized as files for final handoff.

9. `RUNME.md` currently has vague runtime placeholders.
   - It says “roughly seconds per question” rather than measured estimates.
   - Replace with observed ranges:
     - Q4B decomposition: roughly 11-14 seconds per question after model load.
     - Q8B default RICR: roughly 300-500 seconds per question on T4, with MuSiQue long-hop outliers up to about 1100 seconds.
     - Q10 answer generation: roughly 10-11 seconds per question after model load.
     - Q9 ablations vary widely; use the Q9 table values.

10. The notebook still contains “Remove before submission” labels and TODO comments.
    - Do not remove useful run controls. They are important for reproducibility.
    - Instead, rename run-control cells to “Run control / reproducibility helper” and keep them.
    - Remove or relabel purely diagnostic cells that are not needed for grading, such as checkpoint inspection cells, or move their results into the report appendix.
    - Replace scaffold TODO comments only when they make completed code look unfinished.

### Minor Polishing Risks

11. Q1 written response is slightly above the requested 150-200 words.
    - It is 204 words by the notebook count. Trim a sentence if there is time.

12. Q3 currently has two written sections totaling more than the two requested blocks.
    - This is probably acceptable if clearly labeled as “Cross-Dataset Interpretation” and “Hub Explanation,” but the final report should keep them concise.

13. Some notebook tables may be visually truncated in Colab.
    - Use `pd.set_option('display.max_colwidth', None)` and table captions in the report.

## Five-Day Success Plan

### Day 1 - Lock Ownership And Freeze Upload Policy

- Owner A: Questions 1-4 quality pass.
- Owner B: Questions 5-8 completion pass.
- Owner C: Questions 9-12 and reproducibility pass.
- Integrator: only Leping should execute Colab and commit notebook output changes to `main`.
- Teammates should not upload new notebooks to `main`.
- Teammates should submit edits as Markdown snippets, comments, or separate branches. The integrator merges only reviewed content.

Decision rule: after this point, treat `main` as the protected submission branch. Accept teammate work only if it improves rubric coverage and does not overwrite executed outputs.

### Day 2 - Close Q5-Q8

- Q5:
  - Confirm sparse tables include Recall@k, MRR, latency, by-label breakdown, and failure/disagreement examples.
  - If no saved top traces exist, add lightweight JSONL export for top sparse retrieval traces.
- Q6:
  - Verify the FAISS consistency table has five queries per dataset.
  - Verify RRF/dual tables include p95 latency and average candidate count.
  - Add or confirm a route-by-route top-15 explanation for one query helped by dual retrieval.
  - Investigate the small MuSiQue task count if final text depends on it.
- Q7:
  - Run or reconstruct the controlled comparison table from frozen Q6 pools.
  - Produce two top-five before/after traces: reranking improves and reranking worsens.
  - Rewrite Q7 response to cite actual scores and candidate-pool evidence.
- Q8:
  - Run `pytest -q` for supplied tests plus `student_code/test_student_ricr.py`.
  - Add/confirm hand-worked `B=2`, `k=2` beam example.
  - Rewrite Q8 response to cover converging DAG execution, intermediate vs final grouping, and namespaced IDs.

### Day 3 - Close Q9-Q12 Computed Tables Without More Expensive Runs

- Use saved `ricr_traces.jsonl` and `answers.jsonl`.
- Q9:
  - Confirm prediction table, ablation table, and two plots are present.
  - Label `answer_accuracy` precisely. If possible, compute EM/F1 for ablation outputs; otherwise state that the table uses an answer-recovery proxy rather than full answer generation.
- Q10:
  - Add missing metrics that can be derived from traces: average surviving chains, evidence count, latency p95, supporting-document recall if document IDs are present, and answer-context token counts if stored or recomputable.
  - Confirm two trace examples: one successful, one failed with first irreversible error.
- Q11:
  - Add cross-dataset comparison table between 2Wiki and MuSiQue under the frozen configuration.
  - Add transfer-error attribution using counts from saved traces: decomposition failures, retrieval errors, chain-recovery failures, low supporting recall, answer-generation failures.
- Q12:
  - Expand submission JSONL schema to match Section 9.2.
  - Improve `environment.txt` and `RUNME.md`.

### Day 4 - Generate `report.pdf`

- Create a report source file, preferably `report/report.md` or `report/report.tex`.
- Structure by Questions 1-12.
- Keep notebook outputs as the evidence source, but do not paste every table.
- Include:
  - key table/plot for each question;
  - captions with evaluated-question count;
  - brief own-words interpretation;
  - explicit limitations;
  - one-page system story for Q12;
  - two-page appendix for run map, artifact locations, and extra validation output.
- Render to PDF.
- Visual QA:
  - Check page count: <=18 pages excluding references and two-page appendix.
  - Check table readability, captions, axes, units, and no clipped text.

### Day 5 - Final Freeze And Submission

- Sync allowed Colab outputs into `panini-course-project-work/` using `tools/sync_colab_work.py`.
- Run final checks listed below.
- Commit a final freeze.
- No more notebook uploads after final freeze unless a check fails.
- Make a local backup of the final repository zip or commit hash.

## Final Report Plan

Recommended report outline:

1. Title, team, commit hash, compute environment.
2. Q1: package audit and stable ID explanation.
3. Q2: native graph, reconciliation method, audit examples.
4. Q3: network sensitivity, plots, cross-dataset transfer, hub interpretation.
5. Q4: decomposition metrics, error analysis, hand-drawn dependency DAG.
6. Q5: sparse retrieval baselines.
7. Q6: dense/RRF/dual retrieval and route explanation.
8. Q7: reranking comparison and two traces.
9. Q8: RICR algorithm, tests, hand-worked beam.
10. Q9: ablation prediction/result table, trade-off plots, deployment recommendation.
11. Q10: 2Wiki end-to-end metrics and trace analysis.
12. Q11: MuSiQue transfer/scaling and error attribution.
13. Q12: reproducibility, system story, artifact map.
14. References.
15. Appendix A: final run controls and checkpoint paths.
16. Appendix B: validation checklist and JSONL schema examples.

The report should summarize; the notebook remains the reproducible implementation. Do not export the full notebook as the report because it will be too long and too noisy.

## Viable Checks Before Final Submission

Run these checks after every major integration and again at final freeze.

1. Git cleanliness
   - `git status --short`
   - Confirm no unintended teammate notebook overwrite.

2. Static notebook check
   - `python3 tools/static_notebook_check.py`
   - Parse every code cell for syntax errors.

3. Placeholder and confusing-label audit
   - Search for `Write your response`, `TODO`, and `Remove before submission`.
   - Leave intentional scaffold comments only if the implementation below is clearly complete.

4. Tests
   - Run starter tests.
   - Run `student_code/test_student_ricr.py`.
   - Record which supplied RICR tests pass and whether any are skipped.

5. Artifact existence and row counts
   - `cache/2wiki/decompositions.jsonl`: 100 rows.
   - `cache/musique/decompositions.jsonl`: 100 rows.
   - `cache/2wiki/ricr_traces.jsonl`: 100 default rows plus Q9 ablation rows.
   - `cache/musique/ricr_traces.jsonl`: 100 default rows plus Q9 ablation rows.
   - `cache/2wiki/answers.jsonl`: 100 rows.
   - `cache/musique/answers.jsonl`: 100 rows.
   - `submission/results/2wiki_dev.jsonl`: 80 rows.
   - `submission/predictions/2wiki_heldout.jsonl`: 20 rows.
   - `submission/results/musique_dev.jsonl`: 80 rows.
   - `submission/predictions/musique_heldout.jsonl`: 20 rows.

6. JSONL schema check
   - Required for every prediction record:
     - `dataset`
     - `split`
     - `question_id`
     - `question`
     - `predicted_decomposition`
     - `decomposition_valid`
     - `retrieval_backend`
     - `beam_width`
     - `candidates_per_hop`
     - `chains`
     - `evidence_qa_ids`
     - `predicted_answer`
     - `latency_ms`
     - `answer_context_tokens`
   - Development rows may include gold labels and metrics.
   - Held-out rows must not include `answer`, `answer_aliases`, `supporting_facts`, `supporting_document_ids`, `evidences`, or other gold evidence.

7. Forbidden-file check
   - Do not commit `.npy`, `.faiss`, model weights, Hugging Face cache files, full dataset copies, or downloaded package artifacts.
   - Commit only generated outputs, notebook, student code/tests, report, environment, and RUNME.

8. Report checks
   - `report.pdf` exists.
   - Organized by Questions 1-12.
   - <=18 pages excluding references and two-page appendix.
   - Includes one-page system story.
   - Tables/plots have captions, evaluated-question counts, axes labels, and units.

## Thoughts On “Remove Before Submission”

Do not remove run-control cells simply because they were temporary. The rubric explicitly asks for reproducibility, restart points, exact commands, seeds, and a fresh-Colab path. The run map and control cells help satisfy that requirement.

Instead:

- Keep run-control cells, but rename them as reproducibility controls.
- Remove or relabel cells whose only purpose was debugging live Colab state.
- Move useful checkpoint summaries into the report appendix or final validation section.
- Make the final notebook read as a reproducible lab notebook, not as a polished paper. The polished paper is `report.pdf`.

## Recommended Team Policy

- Leping remains the only person who executes Colab and pushes executed notebook/output changes.
- Teammates own written sections and review checklists, not raw notebook uploads.
- Use one of these handoff formats:
  - Markdown snippets per question;
  - Git branches named `review/q5-q8-name`;
  - comments with exact cell names and proposed replacement text.
- Reject uploads that replace the notebook wholesale unless they are rebased from the current `main` and pass the final checks.
- Every accepted teammate contribution must answer a specific rubric item, not merely improve style.

