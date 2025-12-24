from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.schemas.document import DocumentOut
from app.models.document import Document

router = APIRouter(prefix="/admin/documents", tags=["admin"])


@router.get("", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    return db.query(Document).order_by(Document.uploaded_at.desc()).all()


@router.post("", response_model=DocumentOut)
def upload_document(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    from app.services.ingest import ingest_document
    doc = ingest_document(db=db, title=title, file=file, uploaded_by=admin.id)
    return doc


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return {"ok": True}
    db.delete(doc)
    db.commit()
    return {"ok": True}
