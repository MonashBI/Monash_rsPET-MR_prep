#!/usr/bin/env python3
import sys
import os
import os.path as op
import json
from argparse import ArgumentParser
from tqdm import tqdm


parser = ArgumentParser()
parser.add_argument('directory', help="directory containing converted NIfTIs")
parser.add_argument('category', help="The category of the files to edit")
parser.add_argument('contrast', help='The contrast label to edit')
parser.add_argument('--edit', '-e', action='append', nargs=2,
                    metavar=('FIELD', 'VAL'), help="Edit a json field")
args = parser.parse_args()

if not args.edit:
    print("No edits provided!")
    sys.exit()

for subj_dname in tqdm(sorted(d for d in os.listdir(args.directory)
                              if not d.startswith('sub-'))):
    cat_dpath = op.join(args.directory, subj_dname, args.category)
    for fname in os.listdir(cat_dpath):
        bname, ext = op.splitext(fname)
        if ext != '.json' or not bname.endswith(args.contrast):
            continue
        fpath = op.join(cat_dpath, fname)
        with open(fpath) as f:
            js = json.load(f)
        for field, val in args.edit:
            try:
                val = int(val)
            except ValueError:
                try:
                    val = float(val)
                except ValueError:
                    pass
            js[field] = val
        with open(fpath, 'w') as f:
            json.dump(js, f, indent=4)
