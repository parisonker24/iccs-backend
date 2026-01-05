"""Import models so SQLAlchemy's Base.metadata will include them.

This module is intentionally simple: importing it will import all
model modules which register themselves with `app.db.base.Base`.
"""

# Core models
from app.models.user import User  # noqa: F401
from app.models.vendor import Vendor  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.inventory import Inventory  # noqa: F401
from app.models.order import Order  # noqa: F401
from app.models.product_uniform_details import ProductUniformDetails  # noqa: F401
from app.models.product_image import ProductImage  # noqa: F401
from app.models.product_variant import ProductVariant  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.subcategory import Subcategory  # noqa: F401
from app.models.brand import Brand  # noqa: F401
from app.models.product_match_approval import ProductMatchApproval  # noqa: F401

# New canonical product models
from app.models.canonical_product import CanonicalProduct  # noqa: F401
from app.models.canonical_product_embedding import CanonicalProductEmbedding  # noqa: F401
from app.models.canonical_product_minimal import CanonicalProductMinimal  # noqa: F401
from app.models.canonical_product_production import CanonicalProductProduction  # noqa: F401
from app.models.vendor_account import VendorAccount  # noqa: F401
from app.models.vendor_kyc_document import VendorKYCDocument  # noqa: F401

