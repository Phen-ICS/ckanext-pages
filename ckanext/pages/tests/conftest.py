import pytest


@pytest.fixture
def clean_db(reset_db, migrate_db_for):
    reset_db()
    migrate_db_for("pages")


# TEMPORARY diagnostic (see ckanext-pages MR !16): print environment details
# once, on first use, to help pin down why test_revision_restore_page/blog
# fail on the real integration VM but not in 10/10 local runs (both CKAN
# 2.11.5 and 2.12 Docker stacks). Guarded so it only prints once per process
# even though the fixture itself is function-scoped (autouse + session-scope
# would clash with the function-scoped `clean_db`/db fixtures it needs).
_diagnostic_printed = False


@pytest.fixture(autouse=True)
def _print_diagnostic_env_info():
    global _diagnostic_printed
    if not _diagnostic_printed:
        _diagnostic_printed = True
        import sqlalchemy
        from ckan import model

        try:
            version = model.Session.execute(
                sqlalchemy.text("SELECT version()")
            ).scalar()
        except Exception as e:  # noqa: BLE001
            version = f"<could not fetch: {e!r}>"
        print(f"\n[DIAGNOSTIC] Postgres version(): {version}")
        print(f"[DIAGNOSTIC] SQLAlchemy version: {sqlalchemy.__version__}")
    yield
