import pytest
import sqlalchemy as sa
from ckan import model

from ckanext.pages import db


@pytest.fixture
def clean_db(reset_db, migrate_db_for):
    reset_db()
    migrate_db_for("pages")

    # Some test environments rebuild CKAN core tables but skip extension
    # migrations silently. Ensure pages table is present to avoid UndefinedTable.
    inspector = sa.inspect(model.meta.engine)
    if "ckanext_pages" not in inspector.get_table_names():
        db.Page.__table__.create(bind=model.meta.engine, checkfirst=True)


@pytest.fixture
def clean_pages():
    if db.pages_table is not None:
        model.Session.query(db.Page).delete()
        model.Session.commit()
