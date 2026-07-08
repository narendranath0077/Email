from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.database import get_db
from backend import models, schemas
from backend.graph import email_graph
from backend.config import settings

router = APIRouter(prefix="/api", tags=["email"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/generate", response_model=schemas.EmailResponse)
@limiter.limit(settings.RATE_LIMIT)
def generate_email(
    request: Request, payload: schemas.EmailGenerateRequest, db: Session = Depends(get_db)
):
    state = {
        "mode": "generate",
        "purpose": payload.purpose,
        "recipient_name": payload.recipient_name,
        "designation": payload.designation,
        "key_points": payload.key_points,
        "tone": payload.tone,
        "length": payload.length,
    }
    result = email_graph.invoke(state)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    log = models.EmailLog(
        purpose=result["purpose"],
        recipient_name=result["recipient_name"],
        designation=result.get("designation"),
        key_points=result["key_points"],
        tone=result["tone"],
        length=result["length"],
        subject=result["subject"],
        body=result["body"],
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return schemas.EmailResponse(id=log.id, subject=log.subject, body=log.body)


@router.post("/refine", response_model=schemas.EmailResponse)
@limiter.limit(settings.RATE_LIMIT)
def refine_email(
    request: Request, payload: schemas.EmailRefineRequest, db: Session = Depends(get_db)
):
    parent = db.query(models.EmailLog).filter(models.EmailLog.id == payload.email_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Original email not found - try generating again.")

    state = {
        "mode": "refine",
        "previous_subject": parent.subject,
        "previous_body": parent.body,
        "refinement_instruction": payload.refinement_instruction,
        "purpose": parent.purpose,
        "recipient_name": parent.recipient_name,
        "designation": parent.designation,
        "key_points": parent.key_points,
        "tone": parent.tone,
        "length": parent.length,
    }
    result = email_graph.invoke(state)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    log = models.EmailLog(
        purpose=parent.purpose,
        recipient_name=parent.recipient_name,
        designation=parent.designation,
        key_points=parent.key_points,
        tone=parent.tone,
        length=parent.length,
        subject=result["subject"],
        body=result["body"],
        refinement_instruction=payload.refinement_instruction,
        parent_id=parent.id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return schemas.EmailResponse(id=log.id, subject=log.subject, body=log.body)


@router.get("/history", response_model=list[schemas.HistoryItem])
def get_history(limit: int = 20, db: Session = Depends(get_db)):
    logs = (
        db.query(models.EmailLog)
        .order_by(models.EmailLog.id.desc())
        .limit(limit)
        .all()
    )
    return [
        schemas.HistoryItem(
            id=log.id,
            purpose=log.purpose,
            recipient_name=log.recipient_name,
            subject=log.subject,
            created_at=str(log.created_at),
        )
        for log in logs
    ]


@router.get("/email/{email_id}", response_model=schemas.EmailResponse)
def get_email(email_id: int, db: Session = Depends(get_db)):
    log = db.query(models.EmailLog).filter(models.EmailLog.id == email_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Email not found")
    return schemas.EmailResponse(id=log.id, subject=log.subject, body=log.body)