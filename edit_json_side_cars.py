import os
import os.path as op
import json
from pprint import pprint
from argparse import ArgumentParser
import numpy as np
from tqdm import tqdm


parser = ArgumentParser()
parser.add_argument('directory', help="directory containing converted NIfTIs")
args = parser.parse_args()

TR = 2.45
num_slices = 44
incr = TR / num_slices

slice_t = np.arange(0, TR, step=TR / num_slices)
slice_t = np.reshape(slice_t, (-1, 1))
interleaved = list(np.ravel(np.concatenate((slice_t[(num_slices // 2):, :],
                                            slice_t[:(num_slices // 2), :]),
                                           axis=1)))

pprint(interleaved)

for subj_dir in tqdm(os.listdir(args.directory)):
    for i in range(1, 7):
        fname = op.join(args.directory, 'rest-{}.json'.format(i))
        corrected_fname = op.join(args.directory,
                                  'rest-{}-corrected.json'.format(i))
        with open(fname, 'r') as f:
            js = json.load(f)
        js["SliceTiming"] = interleaved
        with open(corrected_fname, 'w') as f:
            json.dump(js, f)
