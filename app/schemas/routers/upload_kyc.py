from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Request, Depends
from uuid import uuid4
from pathlib import Path
import os
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, oauth2_scheme, decode_access_token
from app.crud import crud_user
from app.db.session import get_db
from app.models.user import UserRole
from app.crud.crud_vendor_account import get_vendor_by_email, get_vendor_by_id
from app.models.vendor_kyc_document import VendorKYCDocument, DocumentType

router = APIRouter()

# Allowed types and maximum size
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_CONTENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


@router.post("/upload/kyc-document")
async def upload_kyc_document(
    request: Request,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    token: str = Depends(oauth2_scheme),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a single KYC document (PAN | GST | LICENSE).

    - Accepts a file and a `document_type` form field.
    - Validates file type and size, saves using a UUID filename.
    - Returns a publicly accessible `file_url` (served from `/uploads/kyc_docs/`).
    """

    # Authenticate user and ensure vendor role
    try:
        user_id = int(current_user.id)
    except Exception:
        user_id = current_user.id

    db_user = await crud_user.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to resolve user")

    if db_user.role != UserRole.vendor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only vendors may upload KYC documents")

    # Try to extract vendor_id from token payload; fall back to vendor lookup by user email
    payload = decode_access_token(token) or {}
    payload_vendor_id = payload.get("vendor_id") or payload.get("vendor_account_id") or None

    vendor_by_email = await get_vendor_by_email(db, db_user.email)

    vendor = None
    if payload_vendor_id:
        # Verify the vendor exists and belongs to this user
        vendor_by_id = await get_vendor_by_id(db, str(payload_vendor_id))
        if not vendor_by_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor account from token not found")
        # If there is a vendor record for this user, ensure they match
        if vendor_by_email and str(vendor_by_email.id) != str(vendor_by_id.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token vendor_id does not match authenticated user")
        vendor = vendor_by_id
    else:
        # Use vendor found by email
        if not vendor_by_email:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor profile not found for current user")
        vendor = vendor_by_email

    # Normalize and validate document_type
    doc_type = (document_type or "").strip().upper()
    if doc_type not in {"PAN", "GST", "LICENSE"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document_type. Must be one of: PAN, GST, LICENSE")

    filename = file.filename or ""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File extension not allowed. Allowed: pdf, jpg, jpeg, png")

    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        # Allow some leniency for jpeg variants by checking extension too
        if not (content_type.startswith("image/") and ext in {".jpg", ".jpeg", ".png"}):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported content type")

    # Read file into memory (safe for <= 5MB)
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file uploaded")
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large. Max size is 5MB")

    # Ensure uploads directory exists (relative to project root)
    base_dir = Path(__file__).resolve().parent.parent.parent
    uploads_dir = base_dir / "uploads" / "kyc_docs"
    os.makedirs(uploads_dir, exist_ok=True)

    # Generate unique filename
    unique_name = f"{uuid4().hex}{ext}"
    dest_path = uploads_dir / unique_name

    # Write file
    try:
        with open(dest_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save file: {e}")

    # Build public URL for the saved file. The app mounts uploads at `/uploads`.
    base_url = str(request.base_url).rstrip("/")
    file_url = f"{base_url}/uploads/kyc_docs/{unique_name}"

    # Persist record in vendor_kyc_documents table tagging with vendor_id
    try:
        record = VendorKYCDocument(
            vendor_id=vendor.id,
            document_type=DocumentType[doc_type],
            document_url=file_url,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save document record: {e}")

    return {
        "file_url": file_url,
        "original_filename": filename,
        "document_type": doc_type,
        "vendor_id": str(vendor.id),
    }
