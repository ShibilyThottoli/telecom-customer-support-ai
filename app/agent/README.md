# Lauki Phones FAQ agent

This LangChain agent runs on Amazon Bedrock AgentCore Runtime. It uses
`ChatGroq` (`openai/gpt-oss-20b`) as its language model, loading the Groq API
key from AWS Secrets Manager.

## Request and retrieval flow

- `main.py` loads FAQ records from `lauki_qna.csv`, embeds each complete
  question and answer with FastEmbed, and indexes them in an in-memory
  `InMemoryVectorStore`.
- The `search_faq` tool retrieves up to two relevant FAQ records. It rejects
  weak cosine matches and uses question-title overlap to prefer the FAQ that
  best matches the customer's wording.
- The system prompt guides the agent to answer conversationally, concisely,
  and only with supported facts. The backend supplies recent and relevant
  conversation history in each request.
- The runtime returns `{"result": "..."}`. The FastAPI backend forwards the
  answer and session ID to the React client.

Run normal conversations through the FastAPI backend to use its SQLite chat
memory. Direct runtime invocations do not persist conversation history.

See the [LangChain agents documentation](https://docs.langchain.com/oss/python/langchain/agents)
for the full `create_agent` surface.
