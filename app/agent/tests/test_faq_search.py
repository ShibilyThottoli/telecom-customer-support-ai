import unittest
from types import SimpleNamespace

from faq_search import retrieve_faq_matches


class FakeVectorStore:
    def __init__(self, results):
        self.results = results
        self.query = None
        self.k = None

    def similarity_search_with_score(self, query, k):
        self.query = query
        self.k = k
        return self.results


class FAQSearchTests(unittest.TestCase):
    def test_exact_faq_question_ranks_above_a_nearby_transfer_topic(self):
        carrier_transfer = SimpleNamespace(
            metadata={"question": "How do I transfer my number from another carrier?"}
        )
        ownership = SimpleNamespace(
            metadata={"question": "Can I transfer ownership of my number?"}
        )
        vector_store = FakeVectorStore(
            [(carrier_transfer, 0.678), (ownership, 0.658)]
        )

        results = retrieve_faq_matches(
            vector_store,
            "Can I transfer ownership of my Lauki Phones number?",
        )

        self.assertEqual(results[0], (ownership, 0.658))
        self.assertEqual(vector_store.k, 5)

    def test_weak_matches_are_rejected(self):
        unrelated_sim = SimpleNamespace(
            metadata={"question": "Is SIM replacement chargeable?"}
        )
        vector_store = FakeVectorStore([(unrelated_sim, 0.431)])

        self.assertEqual(
            retrieve_faq_matches(vector_store, "How can I recharge my SIM?"),
            [],
        )

    def test_relevant_document_match_at_cutoff_is_kept(self):
        kyc_documents = SimpleNamespace(
            metadata={"question": "What ID documents are accepted for KYC?"}
        )
        vector_store = FakeVectorStore([(kyc_documents, 0.446)])

        results = retrieve_faq_matches(vector_store, "What documents do I need?")

        self.assertEqual(results, [(kyc_documents, 0.446)])


if __name__ == "__main__":
    unittest.main()
