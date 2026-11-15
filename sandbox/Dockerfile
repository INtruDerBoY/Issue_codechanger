FROM python:3.11-slim

RUN pip install --no-cache-dir pytest langchain-core langgraph langchain-groq python-dotenv streamlit

RUN useradd -m sandboxuser
USER sandboxuser
WORKDIR /repo
