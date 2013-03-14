#!/usr/bin/python

import sys, re

ignore = (
    re.compile(r'^--( |$)'),
)

clean = (
    (re.compile(r'^(\s*((UNIQUE\s+)?KEY|CONSTRAINT))\s+`.*?`\s'), r'\1 ... '),
    (re.compile(r'^(\).*\sENGINE=.*)\sAUTO_INCREMENT=\d+\s'), r'\1 '),
)

group = (
    (re.compile(r'^\s*(((PRIMARY|UNIQUE) )?KEY|CONSTRAINT)\s'), re.compile(r',\s*$'), ''),
)

current = None

for line in sys.stdin:
    line = line.rstrip()
    if any(pat.search(line) for pat in ignore):
        continue
    for pat, rep in clean:
        line = pat.sub(rep, line)
    rules = filter(lambda rule: rule[0].search(line), group)
    if rules:
        rule = rules[0]
        line = rule[1].sub(rule[2], line)
        if current and (current[0] != rule):
            print '\n'.join(sorted(current[1]))
            current = None
        if not current:
            current = (rule, [])
        current[1].append(line)
    else:
        if current:
            print '\n'.join(sorted(current[1]))
            current = None
        print line