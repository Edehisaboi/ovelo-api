from langgraph.graph import StateGraph, END

from application.services.vRecognition.state import State
from application.services.vRecognition.agents import (
    Transcriber,
    Retriever,
    filter_document,
    apply_score_boost,
    CastLookup,
    decide_match,
    Metadata
)
from application.services.vRecognition.edges import (
    should_query_retriever,
    should_process_document,
    should_lookup_actors,
    should_update_score,
    should_generate_metadata,
)
from infrastructure.database.mongodb import MongoCollectionsManager


def create_vrecognition_graph(
    transcriber: Transcriber,
    mongo_db: MongoCollectionsManager
) -> StateGraph:
    retriever = Retriever(mongo_db)
    cast_lookup = CastLookup(mongo_db)
    metadata = Metadata(mongo_db)

    workflow = StateGraph(State)

    workflow.add_node("transcribe_audio", transcriber.run)
    workflow.add_node("retrieve_documents", retriever.retrieve_documents)
    workflow.add_node("filter_candidates", filter_document)
    workflow.add_node("cast_lookup",cast_lookup.annotate_candidates)
    workflow.add_node("boost_scores", apply_score_boost)
    workflow.add_node("decide_match", decide_match)
    workflow.add_node("build_metadata", metadata.build_result_metadata)

    workflow.add_conditional_edges(
        source="transcribe_audio",
        path=should_query_retriever,
        path_map={
            "retrieve_documents": "retrieve_documents",
            END: END,
        },
    )

    workflow.add_conditional_edges(
        source="retrieve_documents",
        path=should_process_document,
        path_map={
            "filter_candidates": "filter_candidates",
            END: END,
        },
    )

    workflow.add_conditional_edges(
        source="filter_candidates",
        path=should_lookup_actors,
        path_map={
            "cast_lookup": "cast_lookup",
            "decide_match": "decide_match",
            END: END,
        },
    )

    workflow.add_conditional_edges(
        source="cast_lookup",
        path=should_update_score,
        path_map={
            "boost_scores": "boost_scores",
            "decide_match": "decide_match",
            END: END,
        },
    )

    workflow.add_edge("boost_scores", "decide_match")

    workflow.add_conditional_edges(
        source="decide_match",
        path=should_generate_metadata,
        path_map={
            "build_metadata": "build_metadata",
            "transcribe_audio": "transcribe_audio",
            END: END,
        },
    )

    workflow.add_edge("build_metadata", END)

    workflow.set_entry_point("transcribe_audio")

    return workflow
