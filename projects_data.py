import csv
import os
import re

from project_categories import PROJECT_CATEGORIES

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

EMPTY_VALUES = {"", "none", "n/a", "na", "unknown"}

# Matches a funding code at the start of a title, e.g. "Lyme 06b" or "Psych 62" -
# generic so it works for categories added later, not just Lyme/Psych.
CODE_RE = re.compile(r"^\S+\s*\d+[a-zA-Z]?")


def _clean(value):
    return (value or "").strip()


def _is_empty(value):
    return _clean(value).lower() in EMPTY_VALUES


def _split_tags(value):
    return [part.strip() for part in _clean(value).split(",") if part.strip() and not _is_empty(part)]


def _extract_code(value):
    match = CODE_RE.search(_clean(value))
    return match.group(0).strip() if match else ""


def _field(row, fields, name):
    column = fields.get(name)
    return _clean(row.get(column)) if column else ""


def _contact_name(row, fields):
    first = _field(row, fields, "first_name")
    last = _field(row, fields, "last_name")
    return " ".join(part for part in [first, last] if part)


def _load_category(category):
    fields = category["fields"]
    path = os.path.join(DATA_DIR, category["file"])
    projects = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            title = _field(row, fields, "title")
            if not title:
                continue

            tags = []
            for column in fields.get("keywords", []):
                tags += _split_tags(row.get(column))

            projects.append({
                "id": f"{category['key']}-{len(projects)}",
                # The project's stable identifying code (e.g. "Lyme 06b"),
                # extracted from its title. This is the value a Collection's
                # own `project_id` field must exactly match to be linked to
                # this project - unrelated to the array-index-based "id"
                # above, which shifts if CSV rows are reordered.
                "project_id": _extract_code(title),
                "category": category["key"],
                "category_label": category["label"],
                "title": title,
                "description": _field(row, fields, "description"),
                "affiliation": _field(row, fields, "affiliation"),
                "tags": tags,
                "contact_name": _contact_name(row, fields),
            })
    return projects


def _attach_collection_links(projects, collections, all_collections):
    """For each project, attach:
      - has_collection: whether ANY collection is linked to it (used for the
        "data uploaded / pending" filter, independent of who's viewing) -
        checked against every collection regardless of visibility.
      - collection_id / collection_name: the actual link target, only set
        when the *current* user is permitted to see that collection (i.e.
        found in the already permission-scoped `collections` list).
    Both are matched the same way: exact equality between the project's
    `project_id` and a collection's own `project_id` field - an explicit
    link set by the collection's owner, not derived from its name.
    """
    def _index_by_project_id(collection_list):
        index = {}
        for collection in collection_list or []:
            key = (collection.get("project_id") or "").strip().lower()
            if key:
                index[key] = collection
        return index

    accessible_index = _index_by_project_id(collections)
    all_index = _index_by_project_id(all_collections)

    for project in projects:
        key = (project.get("project_id") or "").strip().lower()
        accessible_match = accessible_index.get(key) if key else None
        any_match = accessible_match or (all_index.get(key) if key else None)

        project["has_collection"] = bool(any_match)
        project["collection_id"] = accessible_match.get("id") if accessible_match else None
        project["collection_name"] = accessible_match.get("name") if accessible_match else None
    return projects


def get_projects(collections=None, all_collections=None):
    projects = []
    for category in PROJECT_CATEGORIES:
        projects += _load_category(category)
    return _attach_collection_links(projects, collections, all_collections)
