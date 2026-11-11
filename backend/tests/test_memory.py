import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import memory
from memory import (
    build_prompt,
    delete_history,
    load_history,
    load_memory,
    save_turn,
)


class FakeCursor:
    def fetchall(self):
        return []


class RecordingPostgresConnection:
    def __init__(self):
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, query, params=()):
        self.statements.append((query, params))
        return FakeCursor()

    def close(self):
        pass


class ChatMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "memory.sqlite3"
        self.environment = patch.dict(
            os.environ,
            {
                "CHAT_MEMORY_DB_PATH": str(self.database_path),
                "DATABASE_URL": "",
            },
        )
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temp_dir.cleanup()

    def test_recent_and_relevant_older_turns_are_loaded_per_session(self):
        save_turn("tab-a", "My favorite color is cobalt.", "I will remember that.")
        save_turn("tab-a", "Another older topic.", "A different answer.")
        for index in range(6):
            save_turn("tab-a", f"Recent question {index}", f"Recent answer {index}")
        save_turn("tab-b", "My favorite color is green.", "Understood.")

        recent, relevant = load_memory("tab-a", "What color did I prefer?")

        self.assertEqual(len(recent), 6)
        self.assertEqual(recent[-1], ("Recent question 5", "Recent answer 5"))
        self.assertEqual(
            relevant,
            [("My favorite color is cobalt.", "I will remember that.")],
        )
        self.assertEqual(
            load_history("tab-b")[0]["content"],
            "My favorite color is green.",
        )

    def test_prompt_includes_history_and_keeps_first_turn_unchanged(self):
        self.assertEqual(build_prompt("Hello", [], []), "Current user message:\nHello")

        prompt = build_prompt(
            "What color?",
            [("I like cobalt.", "Got it.")],
            [("My favorite color is blue.", "I will remember that.")],
        )

        self.assertIn("Relevant older conversation memory", prompt)
        self.assertIn("Recent conversation history", prompt)
        self.assertTrue(prompt.endswith("Current user message:\nWhat color?"))

    def test_session_memory_can_be_cleared(self):
        save_turn("tab-a", "Question", "Answer")

        delete_history("tab-a")

        self.assertEqual(load_history("tab-a"), [])

    def test_postgres_queries_use_psycopg_placeholders(self):
        connection = RecordingPostgresConnection()
        with (
            patch.dict(os.environ, {"DATABASE_URL": "postgres://example"}),
            patch.object(memory.psycopg, "connect", return_value=connection),
        ):
            save_turn("tab-a", "Question", "Answer")
            load_history("tab-a")
            load_memory("tab-a", "Follow-up")
            delete_history("tab-a")

        parameterized_queries = [
            query for query, params in connection.statements if params
        ]
        self.assertTrue(parameterized_queries)
        self.assertTrue(all("%s" in query for query in parameterized_queries))
        self.assertFalse(any("?" in query for query in parameterized_queries))


if __name__ == "__main__":
    unittest.main()
