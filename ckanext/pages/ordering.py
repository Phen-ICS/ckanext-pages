"""Where a page goes in a menu, and in which order among pages there.

A page's `order` (a string column, kept as is - no migration) holds a
position and a rank in one number:

- position 0 to 4: the slot among the menu's own entries - before the
  first one (0), after the first (1) ... after the fourth (4). Site
  pages: Datasets, Organizations, Groups, About. Organization and group
  pages: their Datasets, Members, About and Activity Stream tabs.
- rank 1 to 9: the order among the pages sharing that position.

Stored as (position + 1) * 10 + rank, so position 0 is 10-19 and
position 4 is 50-59. A value below 10 is from before ranks existed: it's
the position itself, rank 0 (first). Pages with the same position and
rank are ordered by title, so the order never depends on the database.
"""

POSITIONS = range(5)
RANKS = range(1, 10)


def encode(position, rank):
    """The `order` value for a position and a rank, or "" (not in a menu)
    when there's no position."""
    if position in (None, ""):
        return ""
    position = int(position)
    rank = int(rank) if rank not in (None, "") else 1
    if position not in POSITIONS:
        raise ValueError(f"position must be 0-4, got {position}")
    if rank not in RANKS:
        raise ValueError(f"rank must be 1-9, got {rank}")
    return str((position + 1) * 10 + rank)


def decode(order):
    """(position, rank) for an `order` value, or None when the page isn't
    in a menu (or the value isn't a number)."""
    try:
        value = int(order)
    except (TypeError, ValueError):
        return None
    if value < 0:
        return None
    if value < 10:
        return value, 0
    return value // 10 - 1, value % 10


def sort_key(page):
    """Sort key for a page dict (`order`, `title`): position, then rank,
    then title. Pages not in a menu go last."""
    parts = decode(page.get("order"))
    position, rank = parts if parts else (len(POSITIONS), 0)
    return position, rank, (page.get("title") or "").lower()


def tab_css_order(order):
    """CSS `order` of an organization/group page tab. The tabs' own
    entries sit at 100, 200, 300, 400 and the Pages tab at 500 (see the
    read_base.html templates); a page at position n goes at n * 100 + 50
    plus its rank, so 0 lands before the first tab and 4 between the
    fourth one and Pages."""
    parts = decode(order)
    if parts is None:
        return 470
    position, rank = parts
    return position * 100 + 50 + rank
