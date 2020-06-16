#!/usr/bin/env python3
import os
import os.path as op
import json
import csv
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
    'FrameTimesStart': ('0008', '0032'),
}


#'ImageVoxelSize': (('0028', '0030'), ('0018', '0050')),

with open(args.demographics) as f:
    demographics_csv = csv.reader(f)
    

participants = pandas.read_csv(op.join(args.bids_dir, 'participants.tsv'),
                               delimiter='\t')


for i, subject_id in tqdm(enumerate(subject_ids)):
    subj_dir = op.join(args.bids_dir, 'sub-{:02}'.format(i), 'pet')
    dicom_subj_dir = op.join(args.dicom_dir, str(subject_id))
    for run in range(1, 5):
        fpath = op.join(subj_dir,
                        'sub-{:02}_task-rest_run-{}_pet.nii.gz'.format(i, run))
        with open(fpath) as f:
            js = json.load(f)
        js.update(fixed_entries)
        dicom_run_dir = op.join(dicom_subj_dir, 'pet-{}'.format(run))
        frame_times = []
        for dcm_fname in natsorted(d for d in os.listdir(dicom_run_dir)
                                   if d.endswith('.dcm')):
            with open(dcm_fname) as f:
                dcm = pydicom.dcmread(f)
            if not frame_times:
                js['ImageDecayCorrectionTime'] = dcm[('0008', '0031')]
                js['ScanDate'] = dcm[('0008', '0022')]
                js['ScanStart'] = dcm[('0008', '0031')]
                js['TimeZero'] = dcm[('0008', '0031')]
                in_plane_res = dcm[('0028', '0030')].split('/')
                slice_thick = dcm[('0018', '0050')]
                js['ImageVoxelSize'] = in_plane_res + [slice_thick]
            frame_times.append(dcm[('0008', '0032')])
        print(json.dumps(js), indent=4)
        # with open(fpath, 'w') as f:
        #     json.dump(js, f, indent=4)
