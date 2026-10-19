import pytest
from ckan.plugins import toolkit
from ckan.tests import factories, helpers


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "pages")
@pytest.mark.ckan_config("ckanext.pages.editor", "")
class TestOrganizationPagesMenu:
    def _org_page(self, user, org, name, order):
        helpers.call_action(
            "ckanext_org_pages_update",
            {"user": user["name"]},
            org_id=org["id"],
            page=name,
            name=name,
            title=name.title(),
            content="x",
            order=order,
            private=False,
        )

    def test_ordered_org_pages_become_organization_tabs(self, app):
        user = factories.Sysadmin()
        org = factories.Organization()
        self._org_page(user, org, "license", "1")
        self._org_page(user, org, "hidden", "")

        body = app.get(toolkit.url_for("organization.read", id=org["name"])).body

        assert f'/organization/pages/{org["name"]}/license"' in body
        assert f'/organization/pages/{org["name"]}/hidden"' not in body
