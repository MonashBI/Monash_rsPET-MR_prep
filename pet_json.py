#!/usr/bin/env python3
import os
import os.path as op
import re
import json
import csv
import subprocess as sp
from collections import defaultdict
from argparse import ArgumentParser
from natsort import natsorted
import pydicom
from tqdm import tqdm


parser = ArgumentParser()
parser.add_argument('bids_dir', help="directory containing converted NIfTIs")
parser.add_argument('dicom_dir', help="directory containing converted dicoms")
parser.add_argument('demographics', help='The demographics file')
args = parser.parse_args()

subject_ids = [303, 305, 306, 308, 309, 310, 311, 312, 313, 314, 315, 316, 318,
               319, 322, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334,
               335]

fixed_entries = {
    'Modality': 'petmr',
    # 'Manufacturer': 'Siemens',
    # 'ManufacturersModelName': 'Biograph_mMR',
    'BodyPart': 'brain',
    'Unit': 'Bq/ml',
    'TracerName': 'FDG',
    'TracerRadLex': 'RID11701',
    'TracerSNOMED': 'http://purl.bioontology.org/ontology/SNOMEDCT/764660008',
    'TracerRadionuclide': 'F18',
    'TracerMolecularWeight': 181.26,
    'TracerMolecularWeightUnit': 'g/mol',
    'PharmaceuticalDoseUnit': 'Bq/g',
    'PharmaceuticalDoseRegimen': 'IV infusion',
    'PharmaceuticalDoseTime': [0, 90],
    'PharmaceuticalDoseTimeUnit': 's',
    'InjectedRadioactivityUnit': 'MBq',
    'InjectedMassPerWeightUnit': 'MBq/mL',
    'SpecificRadioactivityUnit': 'MBq',
    'ModeOfAdministration': 'infusion',
    'InfusionSpeed': 0.01,
    'InfusionSpeedUnit': 'mL/s',
    'InjectedVolumeUnit': 'mL',
    'FrameTimesStartUnit': 's',
    'FrameDuration': 16,
    'FrameDurationUnit': 's',
    'AcquisitionMode': 'list mode',
    'ImageDecayCorrected': True,
    'DiameterFOV': 258,
    'DiameterFOVUnit': 'mm',
    'ImageOrientation': '3D',
    'ReconMatrixSize': 344,
    'ReconMethodName': '3D Iterative',
    'ReconMethodParameterLabels': ['Subsets', 'iterations', 'zoom'],
    'ReconMethodParameterUnit': ['none', 'none', 'none'],
    'ReconMethodParameterValues': [21, 3, 1],
    'ReconMethodImplementationVersion': 'Syngo VB20 P',
    'ReconFilterType': 'Gaussian',
    'ReconFilterSize': 4,
    'AttenuationCorrection': 'DIXON Brain HiRes',
    'ScatterFraction': 44.32,
    'DecayCorrectionFactor': 1.07238,
    'PlasmaAvail': False,
    # 'PlasmaFreeFractionMethod': 'Counts per minute(CPM)',
    'MetaboliteAvail': False,
    'MetaboliteRecoveryCorrectionApplied': False,
    'ContinuousBloodAvail': False,
    'ContinuousBloodDispersionCorrected': False,
    'BloodDiscreteAvail': False,
    'BloodDiscreteDensity': 'g/dl'
}

# {
# Sex	M / F
# Handedness(Self Report)	Hand dominance - self report
# Years of Educationa	Calculated as formal education of 6 months or more. Starts from the first year of primary / elementary school onwards. Note that Australian education system includes 13 years of school: 7 years primary / elementary, 6 years high school.
# Highest Level Completed b	Calculated as the highest level of formal education completed(i.e., does not include uncompleted education or education currently undertaken). In Australia, 'technical school' is education undertaken in the TAFE / vocational education sector
# English as first language?	Yes / No. For no - first language is reported
# Visual impairment - self report	Yes / No. Further information included for Yes. Any kind of vision impairment including wearing reading glasses
# Personal history of mental illness - self report	Self report of whether the person has had a current or past Axis I psychiatric condition
# Personal history of mental illness - diagnosis or treatment	Whether the person has received a diagnosis for any Axis I psychiatric condition
# History of cadiovascular disease	Yes / No
# History of diabetes	Yes / No
# Regular medication	Yes / No. For yes - further information included
# Current smoker	Yes / No
# Previous smoker	Yes / No
# Average alcohol consumption - self report	Self report alcohol consumption. Includes number of days per week / month the person drinks, and average number of standard drinks per drinking session
# Used recreational drugs in last 6 months	Yes / No
# Drugs - specify	details of drug use
# Edinburgh Handedness: Edinburgh Handedness Inventory
# scores provided for left and right separately
# CESD - R	Centre for Epidemiological Studies Depression Inventory - Revised total score
# Haemoglobin g / dl
# FDG Dose(MBq)
# Infusion Start Time(Clock)
# }

dicom_fields = {
    'ImageDecayCorrectionTime': ('0008', '0031'),
    'ScanDate': ('0008', '0022'),
    'ScanStart': ('0008', '0031'),
    'TimeZero': ('0008', '0031'),
}


FRAME_TIME_FIELD = ('0008', '0032')  # 'FrameTimesStart'
INPLANE_RES_FIELD = ('0028', '0030')
SLICE_THICK_FIELD = ('0018', '0050')


def get_dcm_field(fname, field):
    line = sp.check_output('dcmdump {} | grep ({},{})'.format(fname, *field),
                           shell=True)
    val = re.match(r'.*\[(.*)\]', line).group(1)
    try:
        val = int(val)
    except ValueError:
        try:
            val = float(val)
        except ValueError:
            pass
    return val


demographic_fields = {'InjectedRadioactivity': 'FDG Dose (MBq)',
                      'InjectionStart': 'Infusion Start Time (Clock)',
                      'BloodDiscreteDensity': 'Haemoglobin g/dl'}

participants_fname = op.join(args.bids_dir, 'participants-new.tsv')

demo_for_json = defaultdict(dict)

with open(args.demographics) as f, open(participants_fname, 'w') as f2:
    reader = csv.reader(f)
    writer = csv.writer(f2, delimiter='\t')
    full_col_names = next(reader)
    col_names = next(reader)
    writer.writerow(['participant_id'] + [c for c in col_names if c])
    for i, row in enumerate(reader):
        writer.writerow(['sub-{:02}'.format(i)]
                        + [c for n, c in zip(col_names, row) if n])
        row_dict = dict(zip(full_col_names, row))
        for bids_name, csv_name in demographic_fields.items():
            demo_for_json[i][bids_name] = row_dict[csv_name]


for i, subject_id in tqdm(enumerate(subject_ids, start=1),
                          "processing subjects"):
    subj_dir = op.join(args.bids_dir, 'sub-{:02}'.format(i), 'pet')
    dicom_subj_dir = op.join(args.dicom_dir, str(subject_id))
    with open(op.join(subj_dir,
                      'sub-{:02}_task-rest_run-1_pet.json'.format(i))) as f:
        js = json.load(f)
    js.update(fixed_entries)
    js['FrameTimesStart'] = []
    # Only need to sample every 127 in order to get the frame times
    dcm_fpaths = []
    for run in range(1, 5):
        dicom_run_dir = op.join(dicom_subj_dir, 'pet-{}'.format(run))
        dcm_files = natsorted(op.join(dicom_run_dir, f)
                              for d in os.listdir(dicom_run_dir)
                              if d.endswith('.dcm'))
        dcm_fpaths.append(op.join(dicom_run_dir, f) for f in dcm_files[::127])
    for fpath in tqdm(dcm_fpaths, "processing dicoms"):
        if not js['FrameTimesStart']:
            for bids_name, dcm_field in dicom_fields.items():
                js[bids_name] = get_dcm_field(fpath, dcm_field)
            js['ImageVoxelSize'] = get_dcm_field(
                fpath, INPLANE_RES_FIELD).split('\\') + get_dcm_field(
                    fpath, SLICE_THICK_FIELD)
        js['FrameTimesStart'].append(get_dcm_field(fpath,
                                                   FRAME_TIME_FIELD))
    js.update(demo_for_json[i])
    with open(op.join(subj_dir,
                      'sub-{:02}_task-rest_pet.json'.format(i)), 'w') as f:
        json.dump(js, f, indent=4)
