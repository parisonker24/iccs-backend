from sqlalchemy import create_engine, text

engine = create_engine('postgresql+psycopg2://postgres:postgres123@localhost:5432/iccs')
with engine.connect() as conn:
    r = conn.execute(text('select count(*) from vendor_accounts'))
    print('vendor_accounts count =', r.scalar())
