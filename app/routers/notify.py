from fastapi import APIRouter, Body, HTTPException
from ..db import exec_sql, get_conn

router = APIRouter(prefix="/v1", tags=["notify"])

@router.post("/notify/register-token")
async def register_token(user_id: str, fcm_token: str = Body(..., embed=True), platform: str | None = None):
    # upsert token
    try:
        sql = "
        insert into public.user_devices (user_id, fcm_token, platform)
        values (%s::uuid, %s, %s)
        on conflict (user_id, fcm_token) do update set last_seen_at=now(), platform=excluded.platform;
        "
        await exec_sql(sql, (user_id, fcm_token, platform))
        return {"ok": True}
    except Exception as e:
        raise HTTPException(400, f"register failed: {e}")

@router.post("/notify/unregister-token")
async def unregister_token(user_id: str, fcm_token: str = Body(..., embed=True)):
    sql = "delete from public.user_devices where user_id=%s::uuid and fcm_token=%s;"
    await exec_sql(sql, (user_id, fcm_token))
    return {"ok": True}

@router.get("/notify/tokens")
async def list_tokens(user_id: str):
    sql = "select id, fcm_token, platform, last_seen_at from public.user_devices where user_id=%s::uuid order by last_seen_at desc"
    async with get_conn() as (_, cur):
        await cur.execute(sql, (user_id,))
        rows = await cur.fetchall()
    return {"devices": rows}

from fastapi import Depends
import os
from ..services.fcm import send_fcm
from ..db import get_conn

PROJECT_ID = os.getenv("FCM_PROJECT_ID", "")

@router.post("/notify/send-to-user")
async def send_to_user(user_id: str, title: str, body: str, dog_id: str | None = None):
    # fetch tokens
    async with get_conn() as (_, cur):
        await cur.execute("select fcm_token from public.user_devices where user_id=%s::uuid", (user_id,))
        rows = await cur.fetchall()
    tokens = [r["fcm_token"] for r in rows]
    if not tokens: return {"sent": [], "note": "no tokens"}
    data = {"dog_id": dog_id} if dog_id else {}
    res = send_fcm(PROJECT_ID, tokens, title, body, data=data)
    return res
