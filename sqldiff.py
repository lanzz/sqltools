#!/usr/bin/python

import sys, re

class ParseError(ValueError):
    pass

class Table(object):
    """
    Wrapper for a database table definition
    """

    column_re = re.compile(r'^(?P<name>`.*?`)\s+(?P<def>.*)')
    attribute_re = re.compile(r'^(\s*((UNIQUE\s+)?KEY|CONSTRAINT))\s+(?P<name>`.*?`)\s+(?P<fkey>(FOREIGN\s+KEY\s)?)', re.IGNORECASE)

    def __init__(self, name):
        self.name = name
        self.columns = []
        self.column = {}
        self.attributes = {}
        self.engine = 'InnoDB'
        self.charset = 'utf8'

    def add_column(self, name, definition):
        if name in self.columns:
            raise KeyError(name)
        self.column[name] = definition
        self.columns.append(name)

    def add_attribute(self, line):
        if line.startswith('PRIMARY KEY '):
            name = 'PRIMARY KEY'
        else:
            match = self.attribute_re.match(line)
            if not match:
                raise ValueError(line)
            if match.group('fkey'):
                name = 'FOREIGN KEY %s' % match.group('name')
            else:
                name = '%s %s' % (match.group(1), match.group('name'))

            if name in self.attributes:
                raise KeyError(name)
            line = self.attribute_re.sub(r'\1 \g<fkey>', line)
        self.attributes[name] = line

    def add_line(self, line):
        line = line.strip().rstrip(',')
        match = self.column_re.match(line)
        if match:
            return self.add_column(match.group('name'), line)
        self.add_attribute(line)

    def columns(self):
        for name in self.columns:
            yield name, self.column[name]

    @property
    def create_statement(self):
        definition = '\n  ' + ',\n  '.join(
            [ self.column[name] for name in self.columns ] +
            sorted(self.attributes.values()),
        ) + '\n'
        return 'CREATE TABLE %s (%s) ENGINE=%s DEFAULT CHARSET=%s;\n' % (
            self.name,
            definition,
            self.engine,
            self.charset,
        )

    def add_column_clause(self, name):
        idx = self.columns.index(name)
        after = 'AFTER %s' % self.columns[idx - 1] if idx else 'FIRST'
        return 'ADD COLUMN %s %s' % (self.column[name], after)

    def alter_column_clause(self, name):
        return 'MODIFY COLUMN %s' % self.column[name]

def parse(stream):
    table_start = re.compile(r'^CREATE TABLE (?P<name>`.*?`) \(\s*$', re.IGNORECASE)
    table_end = re.compile(r'^\) ENGINE=(?P<engine>.*?)(\s.*)?\sDEFAULT CHARSET=(?P<charset>.*?)[;\s]', re.IGNORECASE)
    tables = {}
    table = None
    for line in stream:
        match = table_start.match(line)
        if match:
            if table != None:
                raise ParseError(line, table)
            table = Table(match.group('name'))
            continue
        match = table_end.match(line)
        if match:
            if table == None:
                raise ParseError(line)
            table.engine = match.group('engine')
            table.charset = match.group('charset')
            tables[table.name] = table
            table = None
            continue
        if table != None:
            table.add_line(line)
    if table:
        raise ParseError('(eof)')
    return tables

old_schema = parse(open(sys.argv[1], 'r'))
new_schema = parse(open(sys.argv[2], 'r'))

changes = []
changes += [ 'DROP TABLE %s;\n' % table for table in sorted(set(old_schema.iterkeys()) - set(new_schema.iterkeys())) ]

for table_name in sorted(new_schema.iterkeys()):
    new_table = new_schema.get(table_name)
    old_table = old_schema.get(table_name)
    if not old_table:
        # new table, missing in old schema
        changes.append(new_table.create_statement)
        continue
    table_changes = []
    table_changes += [ 'DROP COLUMN %s' % column for column in sorted(set(old_table.columns) - set(new_table.columns)) ]
    table_changes += [ new_table.add_column_clause(column) for column in new_table.columns if column not in old_table.columns ]
    table_changes += [ new_table.alter_column_clause(name) for name in new_table.columns if name in old_table.columns and old_table.column[name] != new_table.column[name] ]
    table_changes += [ 'DROP %s' % name.replace('UNIQUE KEY', 'KEY') for name, attribute in old_table.attributes.iteritems() if attribute not in new_table.attributes.values() ]
    table_changes += [ 'ADD %s' % attribute for attribute in new_table.attributes.values() if attribute not in old_table.attributes.values() ]
    if table_changes:
        changes.append('ALTER TABLE %s\n  %s;\n' % (table_name, ',\n  '.join(table_changes)))

if changes:
    print('SET NAMES utf8;\nSET UNIQUE_CHECKS=0;\nSET FOREIGN_KEY_CHECKS=0;\n')
    print('\n'.join(changes))
    print('-- Finished')
else:
    print('-- No changes')
