import re

import pytest
from ckan.plugins import toolkit
from ckan.tests import factories, helpers

from ckanext.pages import ordering


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
        # Datasets 100, Members 200, About 300, Activity Stream 400, Pages
        # 500: a page at position n, rank r sits at n*100 + 50 + r.
        user = factories.Sysadmin()
        org = factories.Organization()
        self._org_page(user, org, "first", "11")  # position 0, rank 1
        self._org_page(user, org, "last", "52")  # position 4, rank 2
        self._org_page(user, org, "legacy", "1")  # before ranks: position 1

        body = app.get(toolkit.url_for("organization.read", id=org["name"])).body

        assert (
            f'<li style="order: 51"><a href="/organization/pages/{org["name"]}/first"'
            in body
        )
        assert (
            f'<li style="order: 452"><a href="/organization/pages/{org["name"]}/last"'
            in body
        )
        assert (
            f'<li style="order: 150"><a href="/organization/pages/{org["name"]}/legacy"'
            in body
        )
        assert (
            f'li:has(> a[href="/organization/members/{org["name"]}"]) {{ order: 200; }}'
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
        assert "before the first entry of the menu" in body
        assert 'name="order_rank"' in body


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "pages")
@pytest.mark.ckan_config("ckanext.pages.editor", "")
class TestMainMenu:
    def _site_page(self, user, name, title, **fields):
        helpers.call_action(
            "ckanext_pages_update",
            {"user": user["name"]},
            page=name,
            name=name,
            title=title,
            content="x",
            private=False,
            **fields,
        )

    def _menu_links(self, app):
        body = app.get("/").body
        return [
            href
            for href in re.findall(r'<li[^>]*><a href="([^"]+)"', body)
            if href.startswith(
                ("/dataset", "/organization", "/group", "/about", "/pages")
            )
        ]

    def test_pages_go_in_their_position_among_the_menu_entries(self, app):
        user = factories.Sysadmin()
        self._site_page(user, "start", "Start", order_position="0", order_rank="1")
        self._site_page(user, "help", "Help", order_position="1", order_rank="1")
        self._site_page(user, "end", "End", order_position="4", order_rank="1")

        links = self._menu_links(app)

        assert links.index("/pages/start") < links.index("/dataset/")
        assert links.index("/dataset/") < links.index("/pages/help")
        assert links.index("/pages/help") < links.index("/organization/")
        assert links.index("/about") < links.index("/pages/end")

    def test_rank_then_title_order_pages_sharing_a_position(self, app):
        user = factories.Sysadmin()
        self._site_page(user, "b-second", "Beta", order_position="2", order_rank="1")
        self._site_page(user, "a-second", "Alpha", order_position="2", order_rank="1")
        # Saved before ranks existed: position 2, rank 0 - first there.
        self._site_page(user, "first", "Zulu", order="2")
        self._site_page(user, "third", "Gamma", order_position="2", order_rank="5")

        links = self._menu_links(app)
        pages = [link for link in links if link.startswith("/pages/")]

        assert pages == [
            "/pages/first",
            "/pages/a-second",
            "/pages/b-second",
            "/pages/third",
        ]

    def test_form_fields_are_stored_as_one_order(self):
        user = factories.Sysadmin()
        self._site_page(user, "stored", "Stored", order_position="3", order_rank="2")

        page = helpers.call_action("ckanext_pages_show", page="stored")

        assert page["order"] == "42"
        assert ordering.decode(page["order"]) == (3, 2)

    def test_no_position_means_not_in_the_menu(self, app):
        user = factories.Sysadmin()
        self._site_page(user, "hidden", "Hidden", order_position="", order_rank="1")

        assert "/pages/hidden" not in self._menu_links(app)


@pytest.mark.parametrize(
    "order, parts",
    [
        ("", None),
        (None, None),
        ("x", None),
        ("0", (0, 0)),
        ("4", (4, 0)),
        ("11", (0, 1)),
        ("59", (4, 9)),
        ("23", (1, 3)),
    ],
)
def test_decode(order, parts):
    assert ordering.decode(order) == parts


def test_encode_rejects_out_of_range_values():
    with pytest.raises(ValueError):
        ordering.encode("5", "1")
    with pytest.raises(ValueError):
        ordering.encode("1", "0")
