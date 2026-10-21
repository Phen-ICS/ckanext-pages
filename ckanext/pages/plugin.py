import logging
from html import escape as html_escape
from urllib.parse import quote

import ckan.plugins as p
from ckan.lib.helpers import build_nav_main as core_build_nav_main
from ckan.lib.plugins import DefaultTranslation
from ckan.plugins import toolkit as tk

from ckanext.pages import actions, auth, blueprint, ordering
from ckanext.pages import config as cfg

log = logging.getLogger(__name__)


def build_pages_nav_main(*args):

    about_menu = cfg.about_menu()
    group_menu = cfg.group_menu()
    org_menu = cfg.organization_menu()
    root_path = tk.config["ckan.root_path"] or ""

    new_args = []
    for arg in args:
        if arg[0] in "home.about" and not about_menu:
            continue
        if arg[0] in "group.index" and not group_menu:
            continue
        if arg[0] in "organization.index" and not org_menu:
            continue
        new_args.append(arg)

    # do not display any private pages in menu even for sysadmins
    pages_list = tk.get_action("ckanext_pages_list")(
        None, {"order": True, "private": False}
    )

    page_name = ""
    is_current_page = tk.get_endpoint() in (("pages", "show"), ("pages", "blog_show"))

    if is_current_page:
        page_name = tk.request.path.split("/")[-1]

    def page_item(page):
        type_ = "blog" if page["page_type"] == "blog" else "pages"
        name = quote(page["name"])
        title = html_escape(page["title"])
        link = tk.h.literal(f'<a href="{root_path}/{type_}/{name}">{title}</a>')
        if page["name"] == page_name:
            return tk.literal('<li class="active">') + link + tk.literal("</li>")
        return tk.literal("<li>") + link + tk.literal("</li>")

    # Each page goes in its position among the menu's own entries
    # (0: before the first, n: after the n-th - see ordering.py), already
    # sorted by position, rank and title by ckanext_pages_list.
    by_position = {}
    for page in pages_list:
        position, _rank = ordering.decode(page["order"]) or (len(new_args), 0)
        by_position.setdefault(min(position, len(new_args)), []).append(page)

    output = tk.literal("")
    for index in range(len(new_args) + 1):
        for page in by_position.get(index, []):
            output = output + page_item(page)
        if index < len(new_args):
            output = output + core_build_nav_main(new_args[index])

    return output


def pages_group_menu(group_id):
    """Pages of an organization/group that have a "Header Order", in that
    order - shown as tabs in that organization's own nav (e.g. a License
    page per organization). The site header only ever lists site-wide
    pages, so this is where an organization page's order means
    something. Private pages are left to ckanext_pages_list's own rule
    (members only)."""
    user = tk.current_user.name if tk.current_user.is_authenticated else ""
    return tk.get_action("ckanext_pages_list")(
        {"user": user}, {"org_id": group_id, "order": True}
    )


def render_content(content):
    allow_html = cfg.allow_html()
    return tk.h.render_markdown(content, allow_html=allow_html)


def get_wysiwyg_editor():
    return cfg.editor()


def get_recent_blog_posts(number=5, exclude=None):
    blog_list = tk.get_action("ckanext_pages_list")(
        None, {"order_publish_date": True, "private": False, "page_type": "blog"}
    )
    new_list = []
    for blog in blog_list:
        if exclude and blog["name"] == exclude:
            continue
        new_list.append(blog)
        if len(new_list) == number:
            break

    return new_list


class PagesPluginBase(p.SingletonPlugin, DefaultTranslation):
    p.implements(p.ITranslation, inherit=True)


@tk.blanket.auth_functions(
    {
        "ckanext_pages_show": auth.pages_show,
        "ckanext_pages_update": auth.pages_update,
        "ckanext_pages_delete": auth.pages_delete,
        "ckanext_pages_list": auth.pages_list,
        "ckanext_pages_upload": auth.pages_upload,
        "ckanext_org_pages_show": auth.org_pages_show,
        "ckanext_org_pages_update": auth.org_pages_update,
        "ckanext_org_pages_delete": auth.org_pages_delete,
        "ckanext_org_pages_list": auth.org_pages_list,
        "ckanext_group_pages_show": auth.group_pages_show,
        "ckanext_group_pages_update": auth.group_pages_update,
        "ckanext_group_pages_delete": auth.group_pages_delete,
        "ckanext_group_pages_list": auth.group_pages_list,
    }
)
@tk.blanket.helpers(
    {
        "build_nav_main": build_pages_nav_main,
        "render_content": render_content,
        "pages_group_menu": pages_group_menu,
        "pages_order_parts": ordering.decode,
        "pages_tab_css_order": ordering.tab_css_order,
        "pages_get_wysiwyg_editor": get_wysiwyg_editor,
        "get_recent_blog_posts": get_recent_blog_posts,
    }
)
@tk.blanket.blueprints([blueprint.pages])
@tk.blanket.config_declarations
class PagesPlugin(PagesPluginBase):
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IActions, inherit=True)
    p.implements(p.IConfigurable, inherit=True)

    def update_config(self, config):
        self.organization_pages = cfg.enable_organization_pages()
        self.group_pages = cfg.enable_group_pages()

        tk.add_template_directory(config, "theme/templates_main")
        if self.group_pages:
            tk.add_template_directory(config, "theme/templates_group")
        if self.organization_pages:
            tk.add_template_directory(config, "theme/templates_organization")

        tk.add_resource("assets", "pages")

        tk.add_public_directory(config, "assets/")
        tk.add_public_directory(config, "assets/vendor/ckeditor/")
        tk.add_public_directory(config, "assets/vendor/ckeditor/skins/moono-lisa")

    def get_actions(self):
        actions_dict = {
            "ckanext_pages_show": actions.pages_show,
            "ckanext_pages_update": actions.pages_update,
            "ckanext_pages_revision_restore": actions.pages_revision_restore,
            "ckanext_pages_delete": actions.pages_delete,
            "ckanext_pages_list": actions.pages_list,
            "ckanext_pages_upload": actions.pages_upload,
        }
        if self.organization_pages:
            org_actions = {
                "ckanext_org_pages_show": actions.org_pages_show,
                "ckanext_org_pages_update": actions.org_pages_update,
                "ckanext_org_pages_delete": actions.org_pages_delete,
                "ckanext_org_pages_list": actions.org_pages_list,
            }
            actions_dict.update(org_actions)
        if self.group_pages:
            group_actions = {
                "ckanext_group_pages_show": actions.group_pages_show,
                "ckanext_group_pages_update": actions.group_pages_update,
                "ckanext_group_pages_delete": actions.group_pages_delete,
                "ckanext_group_pages_list": actions.group_pages_list,
            }
            actions_dict.update(group_actions)
        return actions_dict


class TextBoxView(p.SingletonPlugin):
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IResourceView, inherit=True)

    def update_config(self, config):
        tk.add_resource("textbox/theme", "textbox")
        tk.add_template_directory(config, "textbox/templates")

    def info(self):
        ignore_missing = tk.get_validator("ignore_missing")
        schema = {
            "content": [ignore_missing],
        }

        return {
            "name": "wysiwyg",
            "title": tk._("Free Text"),
            "icon": "pencil",
            "iframed": False,
            "schema": schema,
        }

    def can_view(self, data_dict):
        return True

    def view_template(self, context, data_dict):
        return "textbox_view.html"

    def form_template(self, context, data_dict):
        return "textbox_form.html"

    def setup_template_variables(self, context, data_dict):
        return
