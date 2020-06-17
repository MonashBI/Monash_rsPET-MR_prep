#!/usr/bin/env python3
import os
import os.path as op
import re
import json
from datetime import datetime
import csv
import subprocess as sp
from collections import defaultdict
from argparse import ArgumentParser
from natsort import natsorted
from tqdm import tqdm


parser = ArgumentParser()
parser.add_argument('bids_dir', help="directory containing converted NIfTIs")
parser.add_argument('dicom_dir', help="directory containing converted dicoms")
parser.add_argument('demographics', help='The demographics file')
parser.add_argument('--just_participants', '-p', action='store_true',
                    default=False,
                    help="Just the participants file not the PET JSONs")
args = parser.parse_args()

subject_ids = [303, 305, 306, 308, 309, 310, 311, 312, 313, 314, 315, 316, 318,
               319, 322, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334,
               335]

fixed_entries = {
    'Modality': 'petmr',
    # 'Manufacturer': 'Siemens',
    # 'ManufacturersModelName': 'Biograph_mMR',
    "InstitutionName": "Monash University",
    "InstitutionalDepartmentName": "Biomedical Imaging",
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
    'ReconMethodParameterLabels': ['subsets', 'iterations', 'zoom'],
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
    line = sp.check_output("dcmdump {} | grep '({},{})'".format(fname, *field),
                           shell=True).decode('utf-8')
    val = re.match(r'.*\[(.*)\]', line).group(1)
    date_match = re.match(r'(201\d)(\d\d)(\d\d)', val)
    if date_match:
        val = ':'.join(date_match.groups())
    else:
        time_match = re.match(r'((?:1|2)\d)(\d\d)(\d\d)', val)
        if time_match:
            val = ':'.join(time_match.groups())
        else:
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

participants_fname = op.join(args.bids_dir, 'participants.tsv')

demo_for_json = defaultdict(dict)


to_delete = ["SeriesDescription", "ProtocolName", "SliceTiming",
             "MultibandAccelerationFactor", "PulseSequenceDetails",
             "PartialFourier"]

with open(args.demographics) as f, open(participants_fname, 'w') as f2:
    reader = csv.reader(f)
    writer = csv.writer(f2, delimiter='\t')
    full_col_names = next(reader)
    col_names = next(reader)
    writer.writerow(['participant_id'] + [c for c in col_names if c])
    for i, row in enumerate(reader, start=1):
        writer.writerow(['sub-{:02}'.format(i)]
                        + [c for n, c in zip(col_names, row) if n])
        row_dict = dict(zip(full_col_names, row))
        for bids_name, csv_name in demographic_fields.items():
            demo_for_json[i][bids_name] = row_dict[csv_name]

if not args.just_participants:
    for i, subject_id in tqdm(enumerate(subject_ids, start=1),
                            "processing subjects"):
        subj_dir = op.join(args.bids_dir, 'sub-{:02}'.format(i), 'pet')
        dicom_subj_dir = op.join(args.dicom_dir, str(subject_id))
        with open(op.join(subj_dir,
                        'sub-{:02}_task-rest_run-1_pet.json'.format(i))) as f:
            js = json.load(f)
        for field in to_delete:
            del js[field]
        js.update(fixed_entries)
        js['FrameTimesStart'] = []
        # Only need to sample every 127 in order to get the frame times
        dcm_fpaths = []
        for run in range(1, 5):
            dicom_run_dir = op.join(dicom_subj_dir, 'pet-{}'.format(run))
            dcm_files = natsorted(op.join(dicom_run_dir, d)
                                for d in os.listdir(dicom_run_dir)
                                if d.endswith('.dcm'))
            dcm_fpaths.extend(op.join(dicom_run_dir, f)
                              for f in dcm_files[::127])
        for fpath in tqdm(dcm_fpaths, "processing dicoms"):
            if not js['FrameTimesStart']:
                for bids_name, dcm_field in dicom_fields.items():
                    js[bids_name] = get_dcm_field(fpath, dcm_field)
                scan_start = datetime.strptime(js['ScanStart'], '%H:%M:%S')
                js['ImageVoxelSize'] = [
                    float(i) for i in str(get_dcm_field(
                        fpath, INPLANE_RES_FIELD)).split('\\')] + [
                    get_dcm_field(fpath, SLICE_THICK_FIELD)]
            frame_start = get_dcm_field(fpath, FRAME_TIME_FIELD)
            frame_start_delta = (datetime.strptime(frame_start, '%H:%M:%S')
                                - scan_start).seconds
            js['FrameTimesStart'].append(frame_start_delta)
        js.update(demo_for_json[i])
        with open(op.join(subj_dir,
                        'sub-{:02}_task-rest_pet.json'.format(i)), 'w') as f:
            json.dump(js, f, indent=4)
