from django.test import TestCase
from unittest.mock import patch

from .rules import hybrid_response
from .llm import llama3_response


class ChatbotTests(TestCase):
    def test_hybrid_response_prefers_rule_reply(self):
        response = hybrid_response('What is phishing?')
        self.assertIn('Phishing is a social engineering attack', response)

    @patch('chatbot.rules.llama3_response')
    def test_hybrid_response_uses_llm_for_generic_question(self, mock_llm):
        mock_llm.return_value = 'LLM fallback answer.'
        response = hybrid_response('Tell me something interesting about phishing scams')
        self.assertEqual(response, 'LLM fallback answer.')
        mock_llm.assert_called_once()

    @patch('chatbot.llm.requests.post')
    def test_llama3_response_returns_none_without_token(self, mock_post):
        # Ensure no API token causes a safe fallback path.
        with patch.dict('os.environ', {}, clear=True):
            self.assertIsNone(llama3_response('How do I identify a phishing email?'))
        mock_post.assert_not_called()
