# SlimZero Examples

This directory contains integration examples for SlimZero.

## Basic Usage

```bash
python basic.py
```

Three-line drop-in integration with mock response.

## Web Frameworks

### Flask

```bash
pip install flask
python flask_example.py
```

POST requests to `/compress` with `{"prompt": "..."}`.

### FastAPI

```bash
pip install fastapi uvicorn
python fastapi_example.py
```

API available at `http://localhost:8000/docs` with Swagger UI.

## LangChain Integration

```bash
pip install langchain-openai
python langchain_example.py
```

Shows integration with LangChain agents and callbacks.

## CLI Usage

```bash
# Direct prompt
python -m slimzero "Explain Python decorators please"

# With system prompt
python -m slimzero "Write a function" --system "You are a coding assistant"

# Show stats
python -m slimzero "Your prompt" --stats
```
