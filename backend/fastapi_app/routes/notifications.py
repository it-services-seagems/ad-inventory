from fastapi import APIRouter

router = APIRouter()


@router.get("/notifications/unread-count")
def unread_count():
    """Simple endpoint that returns a single unread notification for UI testing.

    This is a temporary mock to prevent frontend 404s for the notification bell.
    """
    return {"count": 1}
