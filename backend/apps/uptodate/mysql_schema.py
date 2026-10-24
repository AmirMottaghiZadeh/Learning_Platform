"""Idempotent schema upgrades for the separately managed UpToDate mirror.

Only import/deploy commands call this module; HTTP requests remain read-only.
"""

import pymysql


def _has_title_search_index(cursor) -> bool:
    cursor.execute("SHOW INDEX FROM fts WHERE Index_type = 'FULLTEXT'")
    indexes = {}
    for row in cursor.fetchall():
        indexes.setdefault(row["Key_name"], []).append(row["Column_name"])
    return ["title"] in indexes.values()


def ensure_title_search_index(connection) -> bool:
    """Add the title-only FULLTEXT index to both fresh and existing mirrors.

    MySQL cannot use the old (title, content) index for MATCH(title).
    Existing content and indexes are preserved. Return whether we created it.
    """
    with connection.cursor() as cursor:
        if _has_title_search_index(cursor):
            return False
        try:
            cursor.execute("ALTER TABLE fts ADD FULLTEXT INDEX ft_fts_title (title)")
        except pymysql.err.OperationalError as exc:
            # Another deploy/import may have created it after our check.
            # Only accept a duplicate-name error if the required index exists.
            if exc.args[0] != 1061 or not _has_title_search_index(cursor):
                raise
            return False
    return True
