# FastAPI chat backend

The backend stores completed chat turns in a local SQLite database. Recent
turns provide short-term context; older turns from the same session are
searched by keyword overlap and the best matches are included as long-term
context. No Amazon Bedrock AgentCore Memory resource is used.

The database defaults to `backend/chat_memory.sqlite3`. Set
`CHAT_MEMORY_DB_PATH` to use another file or a mounted persistent volume.
When `DATABASE_URL` is set, the backend uses PostgreSQL instead (for example,
a hosted database in production). The database is scoped by `session_id`: it
supports memory within the same conversation, but does not identify a person
or share memory across new sessions. The frontend keeps the session ID in
`sessionStorage`, so it survives page reloads in the same browser tab and is
discarded when that tab session ends.

`GET /sessions/{session_id}/history` restores the latest 50 exchanges, and
`DELETE /sessions/{session_id}/history` clears that session's memory. To run
the API from this directory, use `uvicorn main:app --reload`.