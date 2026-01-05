from sqlalchemy.orm import declarative_base

# Define SQLAlchemy declarative base here. Do not import models from
# this module — importing models here creates circular import problems
# because models import `Base` from this module.
Base = declarative_base()