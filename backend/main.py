
import json
import logging
import os
import sqlite3
import uuid

import boto3
import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from memory import (
    build_prompt,
    delete_history,
    load_history,
    load_memory,
    save_turn,
)

app = FastAPI()
logger = logging.getLogger(__name__)

cors_origins = [
    origin.strip().rstrip("/")
    for origin in os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REGION = os.environ.get(
    "AWS_REGION",
    os.environ.get("AWS_DEFAULT_REGION", "ap-southeast-2"),
)

AGENT_RUNTIME_ARN = os.environ.get("AGENT_RUNTIME_ARN", (
    "arn:aws:bedrock-agentcore:ap-southeast-2:884730507376:"
    "runtime/ShibilyFAQAssistant_default_agent-GI4xybHUEB"
))

agentcore = boto3.client(
    "bedrock-agentcore",
    region_name=REGION
)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


@app.get("/")
def home():
    return {"message": "Lauki FAQ Assistant API is running"}


@app.post("/chat")
def chat(request: ChatRequest):

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = request.session_id or str(uuid.uuid4())

    try:
        recent_turns, relevant_turns = load_memory(session_id, request.message)
    except (OSError, sqlite3.Error, psycopg.Error) as error:
        logger.exception("Unable to read chat memory")
        raise HTTPException(
            status_code=500,
            detail="Unable to read chat memory"
        ) from error

    try:
        response = agentcore.invoke_agent_runtime(
            agentRuntimeArn=AGENT_RUNTIME_ARN,
            runtimeSessionId=session_id,
            qualifier="DEFAULT",
            contentType="application/json",
            accept="application/json",
            payload=json.dumps({
                "prompt": build_prompt(
                    request.message,
                    recent_turns,
                    relevant_turns
                )
            }).encode("utf-8")
        )

        response_body = response["response"].read().decode("utf-8")
        result = json.loads(response_body)
    except Exception as error:
        logger.exception("AgentCore invocation failed")
        raise HTTPException(
            status_code=502,
            detail="The assistant service couldn't complete the request. Please try again."
        ) from error

    answer = result.get("result") if isinstance(result, dict) else None
    if not isinstance(answer, str) or not answer.strip():
        logger.error("AgentCore returned an empty or invalid answer")
        raise HTTPException(
            status_code=502,
            detail="The assistant returned an empty response. Please try again."
        )

    try:
        save_turn(session_id, request.message, answer)
    except (OSError, sqlite3.Error, psycopg.Error) as error:
        logger.exception("Unable to save chat memory")
        raise HTTPException(
            status_code=500,
            detail="Unable to save chat memory"
        ) from error

    return {
        "answer": answer,
        "session_id": session_id
    }


@app.get("/sessions/{session_id}/history")
def session_history(session_id: str):
    try:
        return {"messages": load_history(session_id)}
    except (OSError, sqlite3.Error, psycopg.Error) as error:
        logger.exception("Unable to load chat history")
        raise HTTPException(
            status_code=500,
            detail="Unable to load chat history"
        ) from error


@app.delete("/sessions/{session_id}/history")
def clear_session_history(session_id: str):
    try:
        delete_history(session_id)
        return {"message": "Session memory cleared"}
    except (OSError, sqlite3.Error, psycopg.Error) as error:
        logger.exception("Unable to clear chat history")
        raise HTTPException(
            status_code=500,
            detail="Unable to clear chat history"
        ) from error
