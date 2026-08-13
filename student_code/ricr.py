"""PANINI connected-DAG RICR implementation for Question 8.

This file is copied into ``panini_course/ricr.py`` by the notebook setup cell.
Keep it versioned in ``student_code`` so Colab resets do not erase the work.
"""

from __future__ import annotations

import itertools
import math
import re
from dataclasses import dataclass, field
from typing import Callable, Mapping, Sequence


PLACEHOLDER_PATTERN = re.compile(r"<ENTITY_Q(\d+)>")
EPSILON = 1e-6


@dataclass(frozen=True)
class Candidate:
    qa_uid: str
    answer_names: tuple[str, ...]
    score: float
    question: str = ""
    answer_ids: tuple[str, ...] = ()
    answer_role_states: tuple[str, ...] = ()
    document_id: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ChainState:
    steps: tuple[Candidate, ...]
    answers_by_step: Mapping[int, tuple[str, ...]]
    score: float
    last_hop_score: float = 0.0

    @property
    def current_answers(self) -> tuple[str, ...]:
        return self.steps[-1].answer_names if self.steps else ()


@dataclass(frozen=True)
class RICRResult:
    components: tuple[tuple[int, ...], ...]
    chains: tuple[ChainState, ...]
    evidence: tuple[Candidate, ...]
    issued_queries: tuple[str, ...]
    fallback: bool = False


def normalize_entity_name(value: str) -> str:
    return " ".join(value.casefold().split())


def normalized_candidate_score(candidate: Candidate) -> float:
    return max(EPSILON, min(1.0, 0.5 * (float(candidate.score) + 1.0)))


def geometric_mean(scores: Sequence[float], epsilon: float = EPSILON) -> float:
    if not scores:
        return 0.0
    safe_scores = [max(float(score), epsilon) for score in scores]
    return float(math.exp(sum(math.log(score) for score in safe_scores) / len(safe_scores)))


def harmonic_mean(scores: Sequence[float], epsilon: float = EPSILON) -> float:
    safe_scores = [max(float(score), epsilon) for score in scores]
    if not safe_scores:
        return epsilon
    return len(safe_scores) / sum(1.0 / score for score in safe_scores)


def panini_chain_score(steps: Sequence[Candidate]) -> float:
    return geometric_mean([normalized_candidate_score(step) for step in steps])


def _requires_retrieval(row: Mapping[str, object]) -> bool:
    return bool(row.get("requires_retrieval", True))


def _question_refs(question: object, upper_bound: int) -> set[int]:
    refs = {int(match) for match in PLACEHOLDER_PATTERN.findall(str(question))}
    return {ref for ref in refs if 1 <= ref <= upper_bound}


def _dependency_graph(
    decomposed_questions: Sequence[Mapping[str, object]],
    retrieval_only: bool,
) -> tuple[dict[int, set[int]], dict[int, set[int]], set[int]]:
    n = len(decomposed_questions)
    if retrieval_only:
        active = {
            idx
            for idx, row in enumerate(decomposed_questions, start=1)
            if _requires_retrieval(row)
        }
    else:
        active = set(range(1, n + 1))

    parents_of: dict[int, set[int]] = {idx: set() for idx in active}
    children_of: dict[int, set[int]] = {idx: set() for idx in active}
    for idx in sorted(active):
        refs = _question_refs(decomposed_questions[idx - 1].get("question", ""), n) - {idx}
        if retrieval_only:
            refs &= active
        parents_of[idx] = refs
        for parent in refs:
            children_of.setdefault(parent, set()).add(idx)
    return parents_of, children_of, active


def _topological_order(
    members: set[int],
    parents_of: Mapping[int, set[int]],
    children_of: Mapping[int, set[int]],
) -> list[int]:
    indegree = {node: len(parents_of.get(node, set()) & members) for node in members}
    available = sorted(node for node, degree in indegree.items() if degree == 0)
    order: list[int] = []

    while available:
        node = available.pop(0)
        order.append(node)
        for child in sorted(children_of.get(node, ()) & members):
            indegree[child] -= 1
            if indegree[child] == 0:
                available.append(child)
        available.sort()

    if len(order) != len(members):
        raise ValueError(f"Cycle detected among decomposition steps {sorted(members)}")
    return order


def identify_retrieval_components(
    decomposed_questions: Sequence[Mapping[str, object]],
) -> list[list[int]]:
    """Return multi-node retrieval components in deterministic DAG order."""

    parents_of, children_of, active = _dependency_graph(decomposed_questions, retrieval_only=True)
    if not active:
        return []

    parent: dict[int, int] = {node: node for node in active}

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for child, refs in parents_of.items():
        for ref in refs:
            union(child, ref)

    groups: dict[int, set[int]] = {}
    for node in active:
        groups.setdefault(find(node), set()).add(node)

    components: list[list[int]] = []
    for members in groups.values():
        if len(members) < 2:
            continue
        components.append(_topological_order(members, parents_of, children_of))

    components.sort(key=lambda component: component[0])
    return components


def instantiate_question(
    template: str,
    answers_by_step: Mapping[int, tuple[str, ...]],
) -> str:
    def replace(match: re.Match[str]) -> str:
        step = int(match.group(1))
        answers = answers_by_step.get(step)
        if not answers:
            raise KeyError(f"Question references unresolved Q{step}: {template}")
        return ", ".join(answers)

    return PLACEHOLDER_PATTERN.sub(replace, template)


def _candidate_sort_key(candidate: Candidate) -> tuple[float, str, tuple[str, ...], tuple[str, ...]]:
    return (-float(candidate.score), candidate.qa_uid, tuple(candidate.answer_ids), tuple(candidate.answer_names))


def _state_signature(state: ChainState) -> tuple[str, ...]:
    return tuple(step.qa_uid for step in state.steps)


def _state_sort_key(state: ChainState) -> tuple[float, float, tuple[str, ...], tuple[str, ...]]:
    answer_names = tuple(name for step in state.steps for name in step.answer_names)
    return (-state.score, -state.last_hop_score, _state_signature(state), answer_names)


def _answer_expansions(candidate: Candidate) -> list[tuple[str, Candidate]]:
    names = tuple(candidate.answer_names)
    ids = tuple(candidate.answer_ids)

    if ids:
        expansions: list[tuple[str, Candidate]] = []
        for idx, answer_id in enumerate(ids):
            selected_name = names[idx] if idx < len(names) else (names[0] if names else answer_id)
            selected = Candidate(
                qa_uid=candidate.qa_uid,
                answer_names=(selected_name,),
                score=candidate.score,
                question=candidate.question,
                answer_ids=(answer_id,),
                answer_role_states=candidate.answer_role_states,
                document_id=candidate.document_id,
                metadata=candidate.metadata,
            )
            expansions.append((f"id::{answer_id}", selected))
        return expansions

    if names:
        return [
            (
                f"name::{normalize_entity_name(name)}",
                Candidate(
                    qa_uid=candidate.qa_uid,
                    answer_names=(name,),
                    score=candidate.score,
                    question=candidate.question,
                    answer_ids=(),
                    answer_role_states=candidate.answer_role_states,
                    document_id=candidate.document_id,
                    metadata=candidate.metadata,
                ),
            )
            for name in names
        ]

    return [(f"qa::{candidate.qa_uid}", candidate)]


def _dedup_steps(states: Sequence[ChainState], final_candidate: Candidate | None = None) -> tuple[Candidate, ...]:
    ordered: list[Candidate] = []
    seen: set[str] = set()
    for state in states:
        for step in state.steps:
            if step.qa_uid in seen:
                continue
            ordered.append(step)
            seen.add(step.qa_uid)
    if final_candidate is not None and final_candidate.qa_uid not in seen:
        ordered.append(final_candidate)
    return tuple(ordered)


def _merge_answers(states: Sequence[ChainState]) -> dict[int, tuple[str, ...]]:
    merged: dict[int, tuple[str, ...]] = {}
    for state in states:
        for step, answers in state.answers_by_step.items():
            merged.setdefault(step, tuple(answers))
    return merged


def _score_steps(steps: Sequence[Candidate]) -> tuple[float, float]:
    return panini_chain_score(steps), normalized_candidate_score(steps[-1]) if steps else 0.0


def _rank_states(states: Sequence[ChainState], beam_width: int) -> tuple[ChainState, ...]:
    return tuple(sorted(states, key=_state_sort_key)[:beam_width])


def _dedup_evidence(states: Sequence[ChainState]) -> tuple[Candidate, ...]:
    evidence: dict[str, Candidate] = {}
    for state in states:
        for candidate in state.steps:
            evidence.setdefault(candidate.qa_uid, candidate)
    return tuple(evidence.values())


def run_panini_ricr(
    decomposed_questions: Sequence[Mapping[str, object]],
    retrieve_and_score: Callable[[str, int], Sequence[Candidate]],
    *,
    original_question: str,
    beam_width: int = 5,
    candidates_per_hop: int = 15,
    multi_dependency_threshold: float = 0.3,
    unique_intermediate_entities: bool = True,
) -> RICRResult:
    """Run PANINI RICR over the connected retrieval DAGs in a decomposition."""

    components = identify_retrieval_components(decomposed_questions)
    issued_queries: list[str] = []
    seen_queries: set[str] = set()
    retrieval_cache: dict[str, tuple[Candidate, ...]] = {}

    def issue(query: str) -> tuple[Candidate, ...]:
        if query not in seen_queries:
            issued_queries.append(query)
            seen_queries.add(query)
        if query not in retrieval_cache:
            retrieval_cache[query] = tuple(
                sorted(retrieve_and_score(query, candidates_per_hop), key=_candidate_sort_key)
            )
        return retrieval_cache[query]

    if not components:
        candidates = issue(original_question)[:beam_width]
        chains = []
        for candidate in candidates:
            steps = (candidate,)
            score, last_hop_score = _score_steps(steps)
            chains.append(
                ChainState(
                    steps=steps,
                    answers_by_step={1: tuple(candidate.answer_names)},
                    score=score,
                    last_hop_score=last_hop_score,
                )
            )
        ranked_chains = _rank_states(chains, beam_width)
        return RICRResult(
            components=(),
            chains=ranked_chains,
            evidence=_dedup_evidence(ranked_chains),
            issued_queries=tuple(issued_queries),
            fallback=True,
        )

    parents_of, children_of, _ = _dependency_graph(decomposed_questions, retrieval_only=True)
    rows = list(decomposed_questions)
    states_by_step: dict[int, tuple[ChainState, ...]] = {}
    final_states: list[ChainState] = []

    for component in components:
        component_set = set(component)
        for node in component:
            template = str(rows[node - 1].get("question", ""))
            retrieval_parents = sorted(parents_of.get(node, set()) & component_set)
            is_sink = not (children_of.get(node, set()) & component_set)
            new_states: list[ChainState] = []

            if not retrieval_parents:
                for candidate in issue(template):
                    for _, selected in _answer_expansions(candidate):
                        steps = (selected,)
                        score, last_hop_score = _score_steps(steps)
                        new_states.append(
                            ChainState(
                                steps=steps,
                                answers_by_step={node: tuple(selected.answer_names)},
                                score=score,
                                last_hop_score=last_hop_score,
                            )
                        )
            elif len(retrieval_parents) == 1:
                parent_node = retrieval_parents[0]
                for parent_state in states_by_step.get(parent_node, ()):
                    query = instantiate_question(template, parent_state.answers_by_step)
                    for candidate in issue(query):
                        expansions = [(None, candidate)] if is_sink else _answer_expansions(candidate)
                        for _, selected in expansions:
                            steps = parent_state.steps + (selected,)
                            answers = {
                                **dict(parent_state.answers_by_step),
                                node: tuple(selected.answer_names),
                            }
                            score, last_hop_score = _score_steps(steps)
                            new_states.append(
                                ChainState(
                                    steps=steps,
                                    answers_by_step=answers,
                                    score=score,
                                    last_hop_score=last_hop_score,
                                )
                            )
            else:
                parent_beams = [states_by_step.get(parent, ()) for parent in retrieval_parents]
                if not all(parent_beams):
                    states_by_step[node] = ()
                    continue

                combo_rows: list[tuple[float, tuple[tuple[str, ...], ...], tuple[ChainState, ...]]] = []
                for combo in itertools.product(*parent_beams):
                    parent_score = harmonic_mean([state.score for state in combo])
                    signature = tuple(_state_signature(state) for state in combo)
                    combo_rows.append((-parent_score, signature, combo))
                combo_rows.sort(key=lambda row: (row[0], row[1]))

                top_combos = combo_rows[:beam_width]
                passing = [
                    combo
                    for neg_score, _, combo in top_combos
                    if -neg_score >= multi_dependency_threshold
                ]
                if not passing and combo_rows:
                    passing = [combo_rows[0][2]]

                for combo in passing:
                    merged_answers = _merge_answers(combo)
                    query = instantiate_question(template, merged_answers)
                    for candidate in issue(query):
                        expansions = [(None, candidate)] if is_sink else _answer_expansions(candidate)
                        for _, selected in expansions:
                            steps = _dedup_steps(combo, selected)
                            answers = {**merged_answers, node: tuple(selected.answer_names)}
                            score, last_hop_score = _score_steps(steps)
                            new_states.append(
                                ChainState(
                                    steps=steps,
                                    answers_by_step=answers,
                                    score=score,
                                    last_hop_score=last_hop_score,
                                )
                            )

            if is_sink:
                ranked = _rank_states(new_states, beam_width)
                states_by_step[node] = ranked
                final_states.extend(ranked)
            elif unique_intermediate_entities:
                best_by_key: dict[str, ChainState] = {}
                for state in new_states:
                    for key, _ in _answer_expansions(state.steps[-1]):
                        current = best_by_key.get(key)
                        if current is None or _state_sort_key(state) < _state_sort_key(current):
                            best_by_key[key] = state
                        break
                states_by_step[node] = _rank_states(tuple(best_by_key.values()), beam_width)
            else:
                states_by_step[node] = _rank_states(new_states, beam_width)

    ranked_final_states = _rank_states(final_states, beam_width)
    return RICRResult(
        components=tuple(tuple(component) for component in components),
        chains=ranked_final_states,
        evidence=_dedup_evidence(ranked_final_states),
        issued_queries=tuple(issued_queries),
        fallback=False,
    )


def run_linear_ricr(
    decomposed_questions: Sequence[Mapping[str, object]],
    retrieve_and_score: Callable[[str, int], Sequence[Candidate]],
    *,
    beam_width: int = 5,
    candidates_per_hop: int = 15,
) -> list[ChainState]:
    first_retrieval_question = next(
        (str(row.get("question", "")) for row in decomposed_questions if _requires_retrieval(row)),
        "",
    )
    return list(
        run_panini_ricr(
            decomposed_questions,
            retrieve_and_score,
            original_question=first_retrieval_question,
            beam_width=beam_width,
            candidates_per_hop=candidates_per_hop,
        ).chains
    )


__all__ = [
    "Candidate",
    "ChainState",
    "RICRResult",
    "geometric_mean",
    "harmonic_mean",
    "identify_retrieval_components",
    "instantiate_question",
    "normalize_entity_name",
    "panini_chain_score",
    "run_linear_ricr",
    "run_panini_ricr",
]
