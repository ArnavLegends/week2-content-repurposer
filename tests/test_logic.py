import unittest

from repurposer.generator import ContentGenerationError, _format_gemini_api_error, parse_output
from repurposer.prompts import build_prompt


class PromptTests(unittest.TestCase):
    def test_prompt_contains_platform_rules_and_source(self):
        prompt = build_prompt(
            article_title="A useful article",
            article_url="https://example.com/article",
            article_text="The article explains a practical idea.",
            audience="New developers",
            tone="Conversational and clear",
            angle="Practical takeaways",
        )
        self.assertIn("X/Twitter", prompt)
        self.assertIn("LinkedIn", prompt)
        self.assertIn("Instagram", prompt)
        self.assertIn("A useful article", prompt)
        self.assertIn("Do not invent statistics", prompt)


class OutputTests(unittest.TestCase):
    def test_parse_valid_output(self):
        raw = '''{"x_thread": ["One", "Two", "Three"], "linkedin_post": "A post.", "instagram_caption": "A caption."}'''
        parsed = parse_output(raw)
        self.assertEqual(len(parsed["x_thread"]), 3)
        self.assertEqual(parsed["linkedin_post"], "A post.")

    def test_reject_invalid_json(self):
        with self.assertRaises(ContentGenerationError):
            parse_output("not json")

    def test_reject_missing_platform_copy(self):
        raw = '''{"x_thread": ["One", "Two", "Three"], "linkedin_post": "", "instagram_caption": "A caption."}'''
        with self.assertRaises(ContentGenerationError):
            parse_output(raw)


class GeminiErrorMessageTests(unittest.TestCase):
    def test_server_error_is_identified_as_service_side(self):
        class FakeApiError(Exception):
            code = 500
            message = "Internal server error"

        message = _format_gemini_api_error(FakeApiError("failure"), "secret-key")
        self.assertIn("HTTP 500", message)
        self.assertIn("service-side", message)
        self.assertNotIn("secret-key", message)

    def test_quota_error_is_actionable(self):
        class FakeApiError(Exception):
            code = 429
            message = "Resource exhausted"

        message = _format_gemini_api_error(FakeApiError("failure"), "secret-key")
        self.assertIn("quota", message.lower())
        self.assertIn("HTTP 429", message)


if __name__ == "__main__":
    unittest.main()
