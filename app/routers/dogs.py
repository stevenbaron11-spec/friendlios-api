from fastapi import APIRouter, Query, HTTPException
from ..db import get_conn

router = APIRouter(prefix="/v1", tags=["dogs"])

@router.get("/dogs/nearby")
async def dogs_nearby(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(10.0, gt=0),
    limit: int = Query(50, gt=0, le=200)
):
    sql = """
    with params as (
      select %s::double precision as lat, %s::double precision as lon, %s::double precision as r_km
    )
    select d.id as dog_id,
           d.display_name,
           d.status,
           d.primary_photo_url,
           p.taken_at as last_seen_at,
           ST_Y(p.geom::geometry) as last_seen_lat,
           ST_X(p.geom::geometry) as last_seen_lon,
           ST_DistanceSphere(p.geom::geometry, ST_SetSRID(ST_MakePoint((select lon from params),(select lat from params)),4326)) / 1000.0 as distance_km
    from public.dogs d
    join public.photos p on p.dog_id = d.id
    where p.geom is not null
      and ST_DWithin(
            p.geom::geography,
            ST_SetSRID(ST_MakePoint((select lon from params),(select lat from params)),4326)::geography,
            (select r_km from params) * 1000.0
          )
    order by distance_km asc, last_seen_at desc
    limit %s;
    """
    async with get_conn() as (_, cur):
        await cur.execute(sql, (lat, lon, radius_km, limit))
        rows = await cur.fetchall()
    return {"results": rows}

@router.get("/dogs/{dog_id}")
async def dog_detail(dog_id: str):
    sql = """
    select d.*, 
           coalesce(d.primary_photo_url, (select url from public.photos where dog_id=d.id order by taken_at desc limit 1)) as photo_url
    from public.dogs d
    where d.id = %s::uuid
    """
    async with get_conn() as (_, cur):
        await cur.execute(sql, (dog_id,))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(404, "Dog not found")
    # recent photos
    sql_ph = "select id, url, taken_at from public.photos where dog_id=%s::uuid order by taken_at desc limit 12;"
    async with get_conn() as (_, cur):
        await cur.execute(sql_ph, (dog_id,))
        photos = await cur.fetchall()
    row["photos"] = photos
    return row
