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

    def test_page_order_places_the_tab_among_the_organization_tabs(self, app):
        # Datasets 10, Members 20, About 30, Activity Stream 40, Pages 50:
        # a page of order n sits at 10n+5.
        user = factories.Sysadmin()
        org = factories.Organization()
        self._org_page(user, org, "first", "0")
        self._org_page(user, org, "last", "4")

        body = app.get(toolkit.url_for("organization.read", id=org["name"])).body

        assert (
            f'<li style="order: 5"><a href="/organization/pages/{org["name"]}/first"'
            in body
        )
        assert (
            f'<li style="order: 45"><a href="/organization/pages/{org["name"]}/last"'
            in body
        )
        assert (
            f'li:has(> a[href="/organization/members/{org["name"]}"]) {{ order: 20; }}'
            in body
        )

    def test_organization_page_form_offers_order_zero(self, app):
        user = factories.Sysadmin()
        org = factories.Organization()

        body = app.get(
            toolkit.url_for("pages.organization_pages_new", id=org["name"]),
            headers={"Authorization": factories.APIToken(user=user["name"])["token"]},
        ).body

        assert '<option value="0"' in body
        assert "0 - before Datasets" in body
