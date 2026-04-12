"""
SlimZero FastAPI Integration Example

Shows how to integrate SlimZero with a FastAPI application.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from slimzero import SlimZero

app = FastAPI(title="SlimZero API", version="1.0")

sz = SlimZero(
    model="gpt-4o",
    token_budget=512,
)


class CompressRequest(BaseModel):
    """Request model for prompt compression."""
    prompt: str
    system_prompt: str | None = None


class CompressResponse(BaseModel):
    """Response model for prompt compression."""
    response: str
    original_tokens: int
    sent_tokens: int
    savings_percent: float
    stages_applied: list[str]


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "SlimZero API", "docs": "/docs"}


@app.post("/compress", response_model=CompressResponse)
def compress(request: CompressRequest):
    """Compress a prompt using SlimZero."""
    try:
        result = sz.call(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
        )

        return CompressResponse(
            response=result.response,
            original_tokens=result.original_input_tokens,
            sent_tokens=result.sent_input_tokens,
            savings_percent=result.input_token_savings_percent,
            stages_applied=result.stages_applied,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def stats():
    """Get cumulative SlimZero statistics."""
    return sz.get_stats()


@app.get("/export/json")
def export_json():
    """Export statistics as JSON."""
    return sz.export_stats_json()


@app.get("/export/markdown")
def export_markdown():
    """Export statistics as Markdown."""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content=sz.export_stats_markdown())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
