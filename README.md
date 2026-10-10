# AI Productivity Coach

An AI-powered productivity assistant built with FastAPI, OpenAI, LangGraph, FAISS, and SQLite.

## Features

* **AI Planner:** Generates structured daily plans with task priorities and time allocations.
* **RAG Assistant:** Answers questions using relevant information from personal notes.
* **Tool-Calling Agent:** Uses a calculator through LangGraph.
* **Plan Management:** Create, retrieve, update, and delete saved plans.
* **Automated Tests:** Tests API endpoints and input validation.

## Tech Stack

* Python
* FastAPI
* OpenAI API
* LangGraph
* FAISS and Sentence Transformers
* SQLAlchemy and SQLite
* Pytest
* Docker

## Setup

1. Clone this repository.

2. Create and activate a Python virtual environment.

3. Install dependencies:

   `pip install -r requirements.txt`

4. Create a `.env` file in the project root:

   `OPENAI_API_KEY=your_api_key_here`

5. Start the API:

   `uvicorn main:app --reload`

6. Open `http://127.0.0.1:8000/docs`.

## Run Tests

`pytest -v`

## Security

Never commit API keys or other secrets to GitHub.