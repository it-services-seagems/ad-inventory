from fastapi import FastAPI

app = FastAPI(title="Notifications Mock", version="0.1")


@app.get("/api/notifications/unread-count")
def unread_count():
    """Return a fixed unread notifications count for UI testing."""
    return {"count": 1}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.notifications_only:app", host="0.0.0.0", port=42060, reload=False)
