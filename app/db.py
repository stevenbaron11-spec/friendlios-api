from contextlib import asynccontextmanager
import psycopg
from psycopg.rows import dict_row
from .config import settings

_pool = None

async def init_db():
    global _pool
    _pool = await psycopg.AsyncConnectionPool.connect(
        conninfo=settings.database_url,
        min_size=1, max_size=10, kwargs={"autocommit": True}
    )

async def close_db():
    if _pool:
        await _pool.close()

@asynccontextmanager
async def get_conn():
    async with _pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            yield conn, cur

async def exec_sql(sql: str, params: tuple | list | None = None):
    async with get_conn() as (_, cur):
        await cur.execute(sql, params or ())

# --- Core RPCs ---
async def rpc_store_photo_embedding(photo_id: str, vec: list[float]):
    sql = "select public.store_photo_embedding(%s, %s::vector);"
    async with get_conn() as (_, cur):
        await cur.execute(sql, (photo_id, f"[{', '.join(map(str, vec))}]"))

async def rpc_match_dogs(vec: list[float], lat: float | None, lon: float | None, k: int = 5):
    sql = """
    select * from public.match_dogs(%s::vector, %s::double precision, %s::double precision, %s::int);
    """
    async with get_conn() as (_, cur):
        await cur.execute(sql, (f"[{', '.join(map(str, vec))}]", lat, lon, k))
        rows = await cur.fetchall()
        return rows

async def rpc_confirm_match(sighting_id: str, chosen_dog_id: str | None, display_name: str | None):
    sql = "select public.confirm_match(%s::uuid, %s::uuid, %s::text);"
    async with get_conn() as (_, cur):
        await cur.execute(sql, (sighting_id, chosen_dog_id, display_name))
        row = await cur.fetchone()
        return row["confirm_match"]

# --- Analysis RPCs ---
async def api_upsert_photo_analysis(photo_id: str, phash_bytes: bytes | None,
                                    lab_hist: list[float] | None,
                                    lbp_hist: list[float] | None,
                                    attributes_json: dict | None):
    sql = "select api.upsert_photo_analysis(%s, %s, %s, %s, %s);"
    await exec_sql(sql, (photo_id, phash_bytes, lab_hist, lbp_hist, attributes_json))

async def api_insert_photo_patch(photo_id: str, part: str, bbox: list[int],
                                 embedding_vec: list[float], score: float) -> None:
    sql = "select api.insert_photo_patch(%s, %s, %s, %s::vector, %s);"
    vec_literal = f"[{', '.join(map(str, embedding_vec))}]"
    await exec_sql(sql, (photo_id, part, bbox, vec_literal, score))

async def api_upsert_dog_part_centroid(dog_id: str, part: str,
                                       centroid_vec: list[float], n_patches: int) -> None:
    sql = "select api.upsert_dog_part_centroid(%s, %s, %s::vector, %s);"
    vec_literal = f"[{', '.join(map(str, centroid_vec))}]"
    await exec_sql(sql, (dog_id, part, vec_literal, n_patches))
