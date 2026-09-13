import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.rag.query_transform import (
    normalize_query,
    is_follow_up_query,
    rewrite_query
)

class TestQueryTransformation(unittest.TestCase):

    def test_standalone_question(self):
        query = "  What is the grading policy for CS101?  "
        orig, rewritten = rewrite_query(query, chat_history=[])
        self.assertEqual(orig, query)
        self.assertEqual(rewritten, "What is the grading policy for CS101?")

    def test_follow_up_question_rewrite(self):
        history = [
            {"role": "user", "content": "We are discussing Topic 162."},
            {"role": "assistant", "content": "Topic 162 covers Production-Grade RAG architecture."}
        ]
        query = "What is its final deliverable?"
        orig, rewritten = rewrite_query(query, chat_history=history)
        self.assertEqual(orig, query)
        self.assertIn("Topic 162", rewritten)
        self.assertIn("final deliverable", rewritten)

    def test_ambiguous_follow_up_without_extractable_topic(self):
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi! How can I help you today?"}
        ]
        query = "What is it?"
        orig, rewritten = rewrite_query(query, chat_history=history)
        # Should fallback safely to normalized query without inventing fake topics
        self.assertEqual(rewritten, "What is it?")

    def test_no_conversation_history(self):
        query = "Explain linear regression."
        orig, rewritten = rewrite_query(query, chat_history=None)
        self.assertEqual(orig, query)
        self.assertEqual(rewritten, "Explain linear regression.")

    def test_technical_terms_and_numbers_preservation(self):
        history = [
            {"role": "user", "content": "Tell me about Unit 3 Process Scheduling."}
        ]
        query = "When is its exam?"
        orig, rewritten = rewrite_query(query, chat_history=history)
        self.assertIn("Unit 3", rewritten)
        self.assertIn("exam", rewritten)

    def test_multi_turn_history_window_cap(self):
        history = [
            {"role": "user", "content": "Topic 10"},
            {"role": "assistant", "content": "Topic 10 content"},
            {"role": "user", "content": "Topic 20"},
            {"role": "assistant", "content": "Topic 20 content"},
            {"role": "user", "content": "We are now studying Topic 162."},
            {"role": "assistant", "content": "Topic 162 is RAG."}
        ]
        query = "What about its requirements?"
        orig, rewritten = rewrite_query(query, chat_history=history)
        self.assertIn("Topic 162", rewritten)
        self.assertNotIn("Topic 10", rewritten)

if __name__ == "__main__":
    unittest.main()
