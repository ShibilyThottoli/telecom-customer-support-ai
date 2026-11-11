import re
from typing import Any


FAQ_CANDIDATE_LIMIT = 5
FAQ_RESULT_LIMIT = 2
FAQ_MIN_SIMILARITY = 0.44
LEXICAL_SCORE_WEIGHT = 0.12

STOP_WORDS = {
    "about",
    "are",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "lauki",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "phones",
    "please",
    "should",
    "the",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "with",
    "would",
    "you",
    "your",
    "sim",
    "add",
    "ons",
}


def _terms(text: str) -> set[str]:
    return {
        term
        for term in re.findall(r"\w{3,}", text.casefold())
        if term not in STOP_WORDS
    }


def retrieve_faq_matches(
    vector_store: Any,
    query: str,
) -> list[tuple[Any, float]]:
    query_terms = _terms(query)
    ranked_results = []

    for document, similarity in vector_store.similarity_search_with_score(
        query,
        k=FAQ_CANDIDATE_LIMIT,
    ):
        if similarity < FAQ_MIN_SIMILARITY:
            continue

        question_terms = _terms(document.metadata.get("question", ""))
        lexical_overlap = (
            len(query_terms & question_terms) / len(query_terms)
            if query_terms
            else 0
        )
        ranked_results.append(
            (document, similarity + LEXICAL_SCORE_WEIGHT * lexical_overlap, similarity)
        )

    ranked_results.sort(key=lambda result: result[1], reverse=True)
    return [
        (document, similarity)
        for document, _, similarity in ranked_results[:FAQ_RESULT_LIMIT]
    ]
