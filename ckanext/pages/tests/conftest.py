import pytest


@pytest.fixture
def clean_db(reset_db, migrate_db_for):
    reset_db()
    migrate_db_for("pages")


# TEMPORARY diagnostic (see ckanext-pages MR !16): print environment details
# on every test, to help pin down why test_revision_restore_page/blog fail
# on the real integration VM but not in 10/10 local runs (both CKAN 2.11.5
# and 2.12 Docker stacks). Deliberately NOT print-once: pytest only shows
# captured stdout for *failed* tests by default (ckanext_test.py doesn't
# pass -s), and a single print during the test_action.py tests (which pass)
# would be silently discarded - printing every test guarantees it shows up
# attached to the two failing ones specifically.
@pytest.fixture(autouse=True)
def _print_diagnostic_env_info():
    import sqlalchemy
    from ckan import model

    try:
        version = model.Session.execute(sqlalchemy.text("SELECT version()")).scalar()
    except Exception as e:  # noqa: BLE001
        version = f"<could not fetch: {e!r}>"
    print(f"\n[DIAGNOSTIC] Postgres version(): {version}")
    print(f"[DIAGNOSTIC] SQLAlchemy version: {sqlalchemy.__version__}")
    yield
