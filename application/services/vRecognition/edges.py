from typing import Union, Any

from langgraph.graph import END

from application.services.vRecognition.state import State


def _valid_state(state: State) -> bool:
    if state.get("end") or state.get("error"):
        return False
    return True

def should_query_retriever(state: State) -> Union[str, Any]:
    if _valid_state(state):
        if state.get("transcript"):
            return "retriever"
    return END

def should_process_document(state: State) -> Union[str, Any]:
    if _valid_state(state):
        if state.get("documents") is not None:
            return "filter"
    return END

def should_query_actors(state: State) -> Union[str, Any]:
    if _valid_state(state):
        if state.get("actors") and state.get("candidates"):
            return "cast_matcher"
        return "decider"
    return END

def should_lookup_actors(state: State) -> Union[str, Any]:
    if _valid_state(state):
        if state.get("actors") and state.get("candidates"):
            return "cast_lookup"
        return "ai_decider"
    return END

def should_update_score(state: State) -> Union[str, Any]:
    if _valid_state(state):
        if state.get("candidates") and state.get("actor_matches"):
            return "booster"
        return "decider"
    return END

def should_generate_metadata(state: State) -> Union[str, Any]:
    if _valid_state(state):
        if state.get("match"):
            return "metadata"
        return "transcriber"
    return END
