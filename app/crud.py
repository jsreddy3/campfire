import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from . import models, schemas
from sqlalchemy.exc import IntegrityError

# Dream ----------------------------------------------------------------
async def create_dream(db: AsyncSession, dream_in: schemas.DreamCreate) -> models.Dream:
    # if the row is already there, return it and bail
    stmt = (
        select(models.Dream)
        .where(models.Dream.id == dream_in.id)
        .options(selectinload(models.Dream.segments))
    )
    if (existing := (await db.execute(stmt)).scalars().first()):
        return existing                         # idempotent path

    # otherwise create as you did before
    dream = models.Dream(id=dream_in.id, title=dream_in.title)
    db.add(dream)
    try:
        await db.commit()                       # succeeds first time
    except IntegrityError:
        await db.rollback()                     # someone beat us—treat as success
    # ensure segments relationship is loaded to avoid lazy-loading in response model
    await db.refresh(dream, attribute_names=["segments"])
    return dream

async def get_dream(db: AsyncSession, dream_id: str) -> models.Dream | None:
    # Use selectinload to explicitly load the segments relationship
    result = await db.execute(
        select(models.Dream)
        .where(models.Dream.id == uuid.UUID(dream_id))
        .options(selectinload(models.Dream.segments))
    )
    return result.scalars().first()

async def list_dreams(db: AsyncSession) -> list[models.Dream]:
    result = await db.execute(select(models.Dream).options(selectinload(models.Dream.segments)))
    return result.scalars().all()

async def update_title(db: AsyncSession, dream_id: str, title: str):
    dream = await get_dream(db, dream_id)
    if dream:
        dream.title = title
        await db.commit()
        return dream
    return None

async def set_state(db: AsyncSession, dream_id: str, state: models.DreamState):
    dream = await get_dream(db, dream_id)
    if dream:
        dream.state = state
        await db.commit()
        # Refresh to get updated state with relationships
        return await get_dream(db, dream_id)
    return None

# AudioSegment ---------------------------------------------------------

async def get_segment(db: AsyncSession, dream_id: str, segment_id: str):
    stmt = select(models.AudioSegment).where(models.AudioSegment.id == uuid.UUID(segment_id), models.AudioSegment.dream_id == uuid.UUID(dream_id))
    result = await db.execute(stmt)
    return result.scalars().first()

async def remove_segment(db: AsyncSession, dream_id: str, segment_id: str):
    stmt = select(models.AudioSegment).where(models.AudioSegment.id == uuid.UUID(segment_id), models.AudioSegment.dream_id == uuid.UUID(dream_id))
    result = await db.execute(stmt)
    seg = result.scalars().first()
    if seg:
        await db.delete(seg)
        await db.commit()
    if not seg:   # already gone? fine.
        return Response(status_code=204)
    return seg
    
async def add_segment(db: AsyncSession, dream_id: str, seg: schemas.AudioSegmentCreate):
    seg_id = uuid.UUID(str(seg.segment_id))     # ← client-supplied
    stmt = select(models.AudioSegment).where(models.AudioSegment.id == seg_id)

    if (existing := (await db.execute(stmt)).scalars().first()):
        print("Segment already stored")
        return existing                         # already stored – idempotent hit

    segment = models.AudioSegment(
        id=seg_id,
        dream_id=uuid.UUID(dream_id),
        filename=seg.filename,
        duration=seg.duration,
        order=seg.order,
        s3_key=seg.s3_key,
    )
    db.add(segment)
    try:
        await db.commit()                       # first arrival
    except IntegrityError:
        await db.rollback()                     # late replay – treat as success
    await db.refresh(segment)
    print("Added segment.")
    return segment