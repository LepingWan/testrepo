import math
import pathlib
import sys


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from ricr import Candidate, identify_retrieval_components, run_panini_ricr


def table_retriever(table):
    def retrieve(query, top_k):
        return list(table.get(query, ()))[:top_k]

    return retrieve


def test_converging_two_parent_dag_matches_notebook_smoke_case():
    plan = [
        {"question": "Who directed Film A?", "requires_retrieval": True},
        {"question": "Who directed Film B?", "requires_retrieval": True},
        {
            "question": "Who was born later, <ENTITY_Q1> or <ENTITY_Q2>?",
            "requires_retrieval": True,
        },
    ]
    table = {
        "Who directed Film A?": [
            Candidate("a1", ("Alice Director",), 0.8, answer_ids=("filmA::e1",))
        ],
        "Who directed Film B?": [
            Candidate("b1", ("Bob Director",), 0.6, answer_ids=("filmB::e1",))
        ],
        "Who was born later, Alice Director or Bob Director?": [
            Candidate("c1", ("Alice Director",), 0.9)
        ],
    }

    result = run_panini_ricr(
        plan,
        table_retriever(table),
        original_question="Who was born later, Film A or Film B director?",
        beam_width=5,
        candidates_per_hop=15,
    )

    expected_score = (0.9 * 0.8 * 0.95) ** (1.0 / 3.0)
    assert result.components == ((1, 2, 3),)
    assert result.issued_queries == (
        "Who directed Film A?",
        "Who directed Film B?",
        "Who was born later, Alice Director or Bob Director?",
    )
    assert [step.qa_uid for step in result.chains[0].steps] == ["a1", "b1", "c1"]
    assert math.isclose(result.chains[0].score, expected_score, rel_tol=0, abs_tol=1e-12)
    assert {candidate.qa_uid for candidate in result.evidence} == {"a1", "b1", "c1"}
    assert result.fallback is False


def test_multi_parent_combo_keeps_best_when_threshold_filters_all():
    plan = [
        {"question": "A?", "requires_retrieval": True},
        {"question": "B?", "requires_retrieval": True},
        {"question": "Compare <ENTITY_Q1> and <ENTITY_Q2>?", "requires_retrieval": True},
    ]
    table = {
        "A?": [Candidate("a1", ("Alpha",), -0.6, answer_ids=("docA::e1",))],
        "B?": [Candidate("b1", ("Beta",), -0.7, answer_ids=("docB::e1",))],
        "Compare Alpha and Beta?": [Candidate("c1", ("Alpha",), 0.2)],
    }

    result = run_panini_ricr(
        plan,
        table_retriever(table),
        original_question="Fallback?",
        beam_width=5,
        candidates_per_hop=10,
        multi_dependency_threshold=0.95,
    )

    assert result.issued_queries[-1] == "Compare Alpha and Beta?"
    assert [step.qa_uid for step in result.chains[0].steps] == ["a1", "b1", "c1"]


def test_intermediate_hop_groups_by_answer_id_and_keeps_best_chain():
    plan = [
        {"question": "Who directed Film A?", "requires_retrieval": True},
        {"question": "Where was <ENTITY_Q1> born?", "requires_retrieval": True},
    ]
    table = {
        "Who directed Film A?": [
            Candidate("a_low", ("Alice",), 0.2, answer_ids=("doc::alice",)),
            Candidate("a_high", ("Alice",), 0.8, answer_ids=("doc::alice",)),
        ],
        "Where was Alice born?": [Candidate("birth", ("Paris",), 0.6)],
    }

    result = run_panini_ricr(
        plan,
        table_retriever(table),
        original_question="Where was Film A director born?",
        beam_width=5,
        candidates_per_hop=10,
    )

    assert [step.qa_uid for step in result.chains[0].steps] == ["a_high", "birth"]


def test_final_hop_keeps_qa_records_without_entity_grouping():
    plan = [
        {"question": "Who directed Film A?", "requires_retrieval": True},
        {"question": "What awards did <ENTITY_Q1> win?", "requires_retrieval": True},
    ]
    table = {
        "Who directed Film A?": [Candidate("a1", ("Alice",), 0.9, answer_ids=("doc::alice",))],
        "What awards did Alice win?": [
            Candidate("award1", ("Best Film",), 0.5, answer_ids=("award::same",)),
            Candidate("award2", ("Best Film",), 0.4, answer_ids=("award::same",)),
        ],
    }

    result = run_panini_ricr(
        plan,
        table_retriever(table),
        original_question="Awards?",
        beam_width=5,
        candidates_per_hop=10,
    )

    final_ids = {state.steps[-1].qa_uid for state in result.chains}
    assert {"award1", "award2"} <= final_ids


def test_document_namespaced_ids_remain_distinct_intermediate_entities():
    plan = [
        {"question": "Who is named Alex?", "requires_retrieval": True},
        {"question": "Where was <ENTITY_Q1> born?", "requires_retrieval": True},
    ]
    table = {
        "Who is named Alex?": [
            Candidate("alex_a", ("Alex",), 0.8, answer_ids=("docA::e1",)),
            Candidate("alex_b", ("Alex",), 0.7, answer_ids=("docB::e1",)),
        ],
        "Where was Alex born?": [Candidate("born", ("Rome",), 0.6)],
    }

    result = run_panini_ricr(
        plan,
        table_retriever(table),
        original_question="Where was Alex born?",
        beam_width=5,
        candidates_per_hop=10,
    )

    root_ids = {state.steps[0].qa_uid for state in result.chains}
    assert {"alex_a", "alex_b"} <= root_ids


def test_singleton_retrieval_plan_falls_back_to_original_question():
    plan = [{"question": "Subquestion?", "requires_retrieval": True}]
    table = {"Original?": [Candidate("direct", ("Answer",), 0.8)]}

    result = run_panini_ricr(
        plan,
        table_retriever(table),
        original_question="Original?",
        beam_width=5,
        candidates_per_hop=10,
    )

    assert result.fallback is True
    assert result.components == ()
    assert result.issued_queries == ("Original?",)
    assert result.chains[0].steps[0].qa_uid == "direct"


def test_deterministic_nodes_are_not_counted_as_retrieval_components():
    plan = [
        {"question": "Who directed Film A?", "requires_retrieval": True},
        {"question": "Use Q1 deterministically", "requires_retrieval": False},
    ]

    assert identify_retrieval_components(plan) == []


def test_evidence_includes_multiple_surviving_final_beams():
    plan = [
        {"question": "Who directed Film A?", "requires_retrieval": True},
        {"question": "Where was <ENTITY_Q1> born?", "requires_retrieval": True},
    ]
    table = {
        "Who directed Film A?": [Candidate("a1", ("Alice",), 0.9, answer_ids=("doc::alice",))],
        "Where was Alice born?": [
            Candidate("birth1", ("Paris",), 0.6),
            Candidate("birth2", ("Lyon",), 0.5),
        ],
    }

    result = run_panini_ricr(
        plan,
        table_retriever(table),
        original_question="Where?",
        beam_width=5,
        candidates_per_hop=10,
    )

    assert {candidate.qa_uid for candidate in result.evidence} == {"a1", "birth1", "birth2"}
