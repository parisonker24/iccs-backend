import asyncio
from app.db.session import async_session_maker
from app.models.vendor import Vendor
import sys

async def main(vendor_id: int):
    async with async_session_maker() as session:
        result = await session.get(Vendor, vendor_id)
        if result is None:
            print(f"Vendor with id={vendor_id} NOT FOUND")
            # Optionally list existing vendor ids
            rows = await session.execute("SELECT id, name FROM vendors LIMIT 10")
            print("Existing vendors (up to 10):")
            for r in rows.fetchall():
                print(r)
            return 1
        print(f"Vendor found: id={result.id}, name={result.name}")
        return 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/check_vendor.py <vendor_id>")
        raise SystemExit(2)
    vendor_id = int(sys.argv[1])
    raise SystemExit(asyncio.run(main(vendor_id)))
