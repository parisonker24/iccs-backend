from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.product import ProductCreate, ProductOut
from typing import List
import traceback

from app.services.embedding_service import get_embedding, cosine_similarity
from app.services.product_matcher import match_products, find_top_matches
from app.services.product_service import get_products_for_user, get_filtered_products_for_matching
from app.crud import crud_product
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.crud import crud_user
from fastapi import Body

router = APIRouter()
DUPLICATE_THRESHOLD = 0.90


@router.post("/", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product_endpoint(
    product_in: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        product_data = product_in.dict()
        product_data['selling_price'] = product_data.pop('price')

        # Step 1: Try to generate embedding
        try:
            product_text = f"{product_in.name} {product_in.description or ''}"
            new_embedding = await get_embedding(product_text)
            product_data['product_embedding'] = new_embedding

            # Step 2: Duplicate Similarity Check
            existing_products = await crud_product.get_products(db, skip=0, limit=1000)
            for product in existing_products:
                if product.product_embedding:
                    try:
                        similarity = cosine_similarity(new_embedding, product.product_embedding)
                        print(f"🔍 Similarity with {product.name}: {similarity}")

                        if similarity > DUPLICATE_THRESHOLD:
                            return {
                                "error": f"Duplicate detected → Similar to '{product.name}' ({similarity:.2f})"
                            }

                    except Exception as e:
                        print(" Similarity comparison failed:", e)
                        traceback.print_exc()
        except Exception as e:
            print(f" Embedding generation failed: {str(e)}. Creating product without embedding.")
            product_data['product_embedding'] = None

        # Step 3: Create Product Record
        created_product = await crud_product.create_product(db, product_data)
        return created_product

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Error creating product: {str(e)}")


@router.post("/match", response_model=dict)
async def match_products_endpoint(new_product: str, existing_product: str):
    """Match one product with another using AI"""
    try:
        result = await match_products(new_product, existing_product)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error matching products: {str(e)}")


@router.post("/find-matches", response_model=List[dict])
async def find_top_matches_endpoint(new_product: str, db: AsyncSession = Depends(get_db)):
    """Suggest similar products for admin approval"""
    try:
        existing_products_result = await crud_product.get_products(db, skip=0, limit=1000)
        existing_products = [
            {"id": p.id, "name": p.name, "description": p.description or ""}
            for p in existing_products_result
        ]

        top_matches = await find_top_matches(new_product, existing_products)
        return top_matches

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error finding matches: {str(e)}")


@router.get("/list", response_model=List[ProductOut])
async def list_products_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List products visible to the current user based on their role"""
    try:
        products = await get_products_for_user(db, current_user.id)
        return products
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error listing products: {str(e)}")


#  TEST ENDPOINT TO VERIFY OPENAI EMBEDDINGS
@router.get("/test-embedding")
async def test_embedding():
    test_text = "Camlin Geometry Box for school students"

    try:
        emb = await get_embedding(test_text)
        return {
            "success": True,
            "message": "Embedding generated successfully ",
            "embedding_length": len(emb)
        }
    except Exception as e:
        print(" Embedding generation failed:", e)
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }



@router.patch("/{product_id}/visibility", response_model=ProductOut)
async def update_product_visibility(
    product_id: int,
    payload: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle product public/private visibility.

    Request body should be JSON: { "is_public": true|false }
    Vendors may only update their own products. Admins may update any product.
    Returns the updated product.
    """

    # Validate payload
    if "is_public" not in payload:
        raise HTTPException(status_code=400, detail="Missing 'is_public' in request body")

    is_public = bool(payload.get("is_public"))

    # Fetch full user from DB to check role
    db_user = await crud_user.get_user(db, int(current_user.id)) if getattr(current_user, "id", None) is not None else None
    if db_user is None:
        raise HTTPException(status_code=401, detail="Unable to resolve current user")

    # Use CRUD layer authorization checks
    product = await crud_product.get_product_for_update(db, product_id, db_user.id, db_user.role)

    # Update and persist
    product.is_public = is_public
    db.add(product)
    await db.commit()
    await db.refresh(product)

    return product
