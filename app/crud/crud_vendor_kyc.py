from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.models.vendor_kyc_document import VendorKYCDocument, DocumentType
from fastapi import HTTPException


async def create_vendor_kyc_documents(db: AsyncSession, vendor_id, documents: List[dict]):
    """Create multiple VendorKYCDocument rows.

    documents: list of dicts with keys: document_type (DocumentType or str), document_url (str)
    """
    created = []
    try:
        for doc in documents:
            doc_type = doc.get('document_type')
            if isinstance(doc_type, str):
                try:
                    doc_type = DocumentType[doc_type]
                except KeyError:
                    raise HTTPException(status_code=400, detail=f"Invalid document_type: {doc.get('document_type')}")
            record = VendorKYCDocument(vendor_id=vendor_id, document_type=doc_type, document_url=doc.get('document_url'))
            db.add(record)
            created.append(record)
        await db.commit()
        for r in created:
            await db.refresh(r)
    except Exception:
        await db.rollback()
        raise
    return created


async def list_vendor_documents(db: AsyncSession, vendor_id):
    result = await db.execute(select(VendorKYCDocument).where(VendorKYCDocument.vendor_id == vendor_id))
    return result.scalars().all()
