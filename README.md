Monash rs-PET-MR Preparation Scripts
====================================

This repository contains a collection of scripts used to edit the JSON side
cars and TSV files in the Monash rs-PET-MR, which has been uploaded to
OpenNeuro (**https://openneuro.org/datasets/ds002898**).


### How to Acknowledge

Cite this paper: 

"Jamadar, S.D., Ward, P.G.D., Close, T.G., Fornito, F., Premaratne, M., O'Brien, K., Staeb, D., Chen, Z., Shah, N.J., Egan, G.F., 2020. 'Monash rsPET-MR'- Simultaneous BOLD-fMRI and constant infusion FDG-PET data of the resting human brain. Scientific Data, 7, 363.

### Axiually Information

**demographics.csv**: It contains the de-identified demographic information of all the subjects

**scan-protocol.pdf**: the scan protocol of the Siemens biograph mMR scanner (software version: B20P)

### Scripts

**edit_bold_json.py**: the script to add 'SliceTiming' information to the json sidecar

**edit_json.py**: the scrip to append extra metadata required by BIDS specification to a json sidecar

**edit_pet_json.py**: the script to add PET related meta data to the json sidecar, according to the PET BIDS specs.

**PrepData_rsfPET_code.m**: The script that applies a convolved spatial-temporal gaussian-weighted gradient operator to the PET data. The details can be seen in figure 5 of the paper (https://www.nature.com/articles/s41597-020-00699-5)
