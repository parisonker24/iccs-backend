# TODO: Implement Duplicate Product Checking with Vector Similarity

## Tasks
- [ ] Add product_embedding field to Product model (app/models/product.py)
- [ ] Add PRODUCT_DUPLICATE_THRESHOLD to config (app/core/config.py)
- [ ] Modify create_product function to check for duplicates (app/crud/crud_product.py)
- [ ] Create Alembic migration for product_embedding field if needed
- [ ] Test the duplicate detection logic
