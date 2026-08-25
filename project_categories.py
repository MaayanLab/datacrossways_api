"""
Single registry of the spreadsheets that populate the Projects page.

To add a new project category:
  1. Drop its CSV into data/.
  2. Add an entry below mapping its column names to the fields the page
     expects ("keywords" can list more than one column - all of them are
     merged into that project's tag list).

No other code changes are needed. The Projects page, its category filter,
and its keyword filter are all built from whatever this list contains.
"""

PROJECT_CATEGORIES = [
    {
        "key": "lyme",
        "label": "Lyme Disease",
        "file": "project_info_lyme.csv",
        "fields": {
            "title": "Title",
            "description": "Description",
            "affiliation": "Affiliation",
            "first_name": "First Name",
            "last_name": "Last Name",
            "keywords": ["Keyword"],
        },
    },
    {
        "key": "psych",
        "label": "Psychedelic Research",
        "file": "project_info_psych.csv",
        "fields": {
            "title": "Title",
            "description": "Description",
            "affiliation": "Affiliation",
            "first_name": "First Name",
            "last_name": "Last Name",
            "keywords": ["Keyword - compound", "Keyword - indication"],
        },
    },
]
