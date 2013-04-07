sqlnorm
=======

A normalizing filter for easier comparison of SQL dumps

---

This filter normalizes SQL dumps for clearer schema comparison, smoothing out meaningless irregularities and
avoiding many common false diffs.

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



sqldiff
=======

Compares the `mysqldump` outputs for two databases, and produces the SQL statements needed to bring
the second database's schema to the same state as the first.

---

_DISCLAIMER:_ This is not a general-purpose comparison tool for _any_ SQL dump.
It relies _heavily_ on the actual format produced by the standard `mysqldump` tool
and will most likely crash and burn if fed SQL generated by other tools.
It has a _very_ limited understanding of the actual structure of the dumps; it just collects each table's definitions,
barely managing to distinguish between column definitions and additional constraints and indexes.
It will happily consider renamed columns as one column dropped and another added —
this _will_ lose the data in the renamed column, if used blindly. It will disregard any reordering of existing columns,
but it will try to preserve the position of new columns.

It is not intended to be used as an automated database schema synchronization tool; rather, it is meant to simplify
comparison of two database schema states, and to _assist_ with the preparation of the SQL needed to get them in sync.
It is still your responsibility to examine the generated SQL, determine if it will break your data,
and amend it as necessary before applying it over your existing data. It is always a good idea to keep a backup.

It does not work with the database contents in any way. It will not compare contents and keep contents in sync.
It only tries to help with managing the schema itself.

Example usage:

    sqldiff.py \
        <( mysqldump --no-data database1 | ./sqlnorm.py ) \
        <( mysqldump --no-data database2 | ./sqlnorm.py )
