from pydantic import BaseModel, ConfigDict

from typing import List, Optional


class ProductCreate(BaseModel):
	name: str
	description: Optional[str] = None
	price: float
	vendor_id: Optional[int] = None
	sku: Optional[str] = None
	hsn_code: Optional[str] = None
	category_id: Optional[int] = None
	sub_category_id: Optional[int] = None
	unit: Optional[str] = None
	vendor_price: Optional[float] = None
	discount_percentage: Optional[float] = 0.0
	stock_count: Optional[int] = 0
	visibility: Optional[bool] = True
	is_public: Optional[bool] = False
	meta_title: Optional[str] = None
	meta_description: Optional[str] = None
	seo_keywords: Optional[dict] = None
	warranty: Optional[str] = None


class ProductOut(BaseModel):
	id: int
	name: str
	description: Optional[str] = None
	selling_price: float
	vendor_id: Optional[int] = None
	sku: Optional[str] = None
	hsn_code: Optional[str] = None
	category_id: Optional[int] = None
	sub_category_id: Optional[int] = None
	unit: Optional[str] = None
	vendor_price: Optional[float] = None
	discount_percentage: Optional[float] = 0.0
	stock_count: Optional[int] = 0
	visibility: Optional[bool] = True
	is_public: Optional[bool] = False
	meta_title: Optional[str] = None
	meta_description: Optional[str] = None
	seo_keywords: Optional[dict] = None
	warranty: Optional[str] = None

	# Use Pydantic v2 style ConfigDict for ORM compatibility
	# equivalent to: class Config: orm_mode = True (pydantic v1)
	product_embedding: Optional[List[float]] = None
	model_config = ConfigDict(from_attributes=True)


class ProductSimilarity(BaseModel):
	id: int
	name: str
	description: Optional[str] = None
	selling_price: float
	similarity_score: float

	model_config = ConfigDict(from_attributes=True)

