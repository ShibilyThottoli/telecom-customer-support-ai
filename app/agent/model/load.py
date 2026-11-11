import json
import boto3
from langchain_groq import ChatGroq

AWS_REGION = "ap-southeast-2"
GROQ_SECRET_NAME = "lauki-finance/groq-api-key"


def load_model():
    """Load Groq API key from AWS Secrets Manager and initialize Groq."""

    client = boto3.client(
        "secretsmanager",
        region_name=AWS_REGION
    )

    response = client.get_secret_value(
        SecretId=GROQ_SECRET_NAME
    )

    secret = response["SecretString"]

    try:
        secret_data = json.loads(secret)
        api_key = secret_data["GROQ_API_KEY"]
    except json.JSONDecodeError:
        api_key = secret

    return ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0,
        api_key=api_key
    )