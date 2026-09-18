import io
import zipfile
from uuid import UUID

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, s3_utils, schemas
from .database import Base, engine, get_db

app = FastAPI(title="Photobooth API")

# Crea las tablas si no existen (events, photos)
Base.metadata.create_all(bind=engine)


@app.post("/events", response_model=schemas.EventCreateResponse)
def create_event(payload: schemas.EventCreate, db: Session = Depends(get_db)):
    event = models.Event(
        client_name=payload.client_name,
        event_type=payload.event_type,
        event_date=payload.event_date,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return schemas.EventCreateResponse(event_id=event.id)


@app.post("/upload", response_model=schemas.UploadResponse)
async def upload_photo(
    event_id: UUID = Form(...),
    message: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    event = db.get(models.Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    image_bytes = await file.read()

    original_key, polaroid_key = s3_utils.upload_original_and_polaroid(
        str(event_id), image_bytes, message
    )

    photo = models.Photo(
        event_id=event_id,
        message=message,
        original_key=original_key,
        polaroid_key=polaroid_key,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)

    return schemas.UploadResponse(photo_id=photo.id, polaroid_key=polaroid_key)


@app.get("/events/{event_id}", response_model=schemas.EventDetailResponse)
def get_event(event_id: UUID, db: Session = Depends(get_db)):
    event = db.get(models.Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    photo_count = (
        db.query(func.count(models.Photo.id))
        .filter(models.Photo.event_id == event_id)
        .scalar()
    )

    return schemas.EventDetailResponse(
        event_id=event.id,
        client_name=event.client_name,
        event_type=event.event_type,
        event_date=event.event_date,
        created_at=event.created_at,
        photo_count=photo_count,
    )


@app.post("/finish")
def finish_event(event_id: UUID = Form(...), db: Session = Depends(get_db)):
    event = db.get(models.Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    photos = db.query(models.Photo).filter(models.Photo.event_id == event_id).all()
    if not photos:
        raise HTTPException(status_code=400, detail="El evento no tiene fotos")

    # Empaqueta las polaroids en un .zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for photo in photos:
            data = s3_utils.download_bytes(photo.polaroid_key)
            filename = photo.polaroid_key.split("/")[-1]
            zf.writestr(filename, data)
    zip_buffer.seek(0)

    # Elimina las fotos originales (quedan solo las polaroids)
    for photo in photos:
        if photo.original_key:
            s3_utils.delete_object(photo.original_key)
            photo.original_key = None
    db.commit()

    headers = {"Content-Disposition": f'attachment; filename="evento_{event_id}.zip"'}
    return StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)
