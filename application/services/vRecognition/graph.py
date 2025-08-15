from langgraph.graph import StateGraph, END

from application.services.vRecognition.state import State
from application.services.vRecognition.agents import (
    Transcriber,
    Retriever,
    CastMatcher,
    Decider,
    Metadata,
    process_document,
    update_score,
)
from application.services.vRecognition.edges import (
    should_query_retriever,
    should_process_document,
    should_query_actors,
    should_update_score,
    should_generate_metadata,
)
from infrastructure.database.mongodb import MongoCollectionsManager


def create_vrecognition_graph(
    transcriber:    Transcriber,
    mongo_db:       MongoCollectionsManager
) -> StateGraph:
    retriever       = Retriever(mongo_db)
    cast_matcher    = CastMatcher(mongo_db)
    decider         = Decider()
    metadata        = Metadata(mongo_db)

    workflow = StateGraph(State)

    workflow.add_node("transcriber",    transcriber.run)
    workflow.add_node("retriever",      retriever.execute)
    workflow.add_node("filter",         process_document)
    workflow.add_node("cast_matcher",   cast_matcher.execute)
    workflow.add_node("booster",        update_score)
    workflow.add_node("decider",        decider.decide)
    workflow.add_node("metadata",       metadata.extract)

    workflow.add_conditional_edges(
        source="transcriber",
        path=should_query_retriever,
        path_map={
            "retriever": "retriever",
            END: END,
        },
    )

    workflow.add_conditional_edges(
        source="retriever",
        path=should_process_document,
        path_map={
            "filter": "filter",
            END: END,
        },
    )

    workflow.add_conditional_edges(
        source="filter",
        path=should_query_actors,
        path_map={
            "cast_matcher": "cast_matcher",
            "decider": "decider",
            END: END,
        },
    )

    workflow.add_conditional_edges(
        source="cast_matcher",
        path=should_update_score,
        path_map={
            "booster": "booster",
            "decider": "decider",
            END: END,
        },
    )

    workflow.add_edge("booster", "decider")

    workflow.add_conditional_edges(
        source="decider",
        path=should_generate_metadata,
        path_map={
            "metadata": "metadata",
            "transcriber": "transcriber",
            END: END,
        },
    )

    workflow.add_edge("metadata", END)

    workflow.set_entry_point("transcriber")

    return workflow
