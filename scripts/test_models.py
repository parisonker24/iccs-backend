from app.models import User, Vendor, CanonicalProduct
print('Imported models')
try:
    u = User(username='u', email='e', hashed_password='p')
    print('Instantiated User ok')
except Exception as e:
    print('Error instantiating User:', e)

try:
    cp = CanonicalProduct(name='cp')
    print('Instantiated CanonicalProduct ok; has vendor_id attr:', hasattr(cp,'vendor_id'))
except Exception as e:
    print('Error instantiating CanonicalProduct:', e)
