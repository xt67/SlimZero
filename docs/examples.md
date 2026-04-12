# Examples

## Basic Usage

See [examples/basic.py](https://github.com/xt67/SlimZero/blob/main/examples/basic.py)

```python
from slimzero import SlimZero

sz = SlimZero(model="mock")
result = sz.call(prompt="Explain Python decorators please")
```

## Flask Integration

See [examples/flask_example.py](https://github.com/xt67/SlimZero/blob/main/examples/flask_example.py)

```bash
pip install flask
python flask_example.py
```

## FastAPI Integration

See [examples/fastapi_example.py](https://github.com/xt67/SlimZero/blob/main/examples/fastapi_example.py)

```bash
pip install fastapi uvicorn
python fastapi_example.py
```

API docs at `http://localhost:8000/docs`

## LangChain Integration

See [examples/langchain_example.py](https://github.com/xt67/SlimZero/blob/main/examples/langchain_example.py)

```bash
pip install langchain-openai
python langchain_example.py
```

## CLI Usage

```bash
# Basic
slimzero "Explain machine learning"

# With system prompt
slimzero "Write a function" --system "You are a coding assistant"

# Show statistics
slimzero "Your prompt" --stats

# Export to file
slimzero "Your prompt" --export-json stats.json
```
