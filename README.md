sqlnorm
=======

A normalizing filter for easier comparison of SQL dumps

---

This filter normalizes SQL dumps for clearer schema comparison, smoothing out meaningless irregularities and avoiding many common false diffs.

Only MySQL dumps have been tested for now; PostgreSQL support will be likely added in the future.

1. All comments and trailing whitespace are stripped — MySQL outputs some varying details about the dump in comments
(timestamp, server version), which are non-essential and are pointless to diff.
2. All key and constraint names are replaced by '...' — they do not alter the behavior of the DB schema, they are often
generated implicitly, and might differ between two databases without representing any meaningful difference.
3. Each group of key- and constraint-related clauses within `CREATE TABLE` statements are sorted and their trailing commas
are stripped — the order of the keys does not matter to the schema but will throw off the diff, and the absence of the comma
in the last clause in a `CREATE TABLE` avoids a false diff as well.
4. All `AUTO_INCREMENT=#` clauses are stipped — those reflect the number of records inserted in the table, and not the
actual structure of the table itself.

The output from this filter is _not_ valid SQL in any way. It is solely intended for easier diffing.

Example usage:

    vimdiff \
        <( mysqldump --no-data database1 | ./sqlnorm.py ) \
        <( mysqldump --no-data database2 | ./sqlnorm.py )