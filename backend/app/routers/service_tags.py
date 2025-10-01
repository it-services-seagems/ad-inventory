from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get('/service-tag/{service_tag}/last-user')
async def service_tag_last_user(service_tag: str, days: int = 30):
    # Placeholder implementation; full implementation requires ADEventLog service
    raise HTTPException(status_code=501, detail='Not implemented in migration')

@router.get('/{service_tag}/last-user')
async def service_tag_last_user_alt(service_tag: str, days: int = 30):
    raise HTTPException(status_code=501, detail='Not implemented in migration')
