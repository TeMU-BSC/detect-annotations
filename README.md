# Detect new annotations in Text files based on TSV with codes and spans.

## Getting Started

Scripts written in Python 3.7, anaconda distribution Anaconda3-2019.07-Linux-x86_64.sh

### Prerequisites

See prerrequisites.txt file.
(You need to have installed python3 and its base libraries, plus:
+ spacy
+ pandas
+ datetime
+ shutil
+ numpy

### Installing

```
git clone <repo_url>
```

## Running the scripts

```
cd detect_annotations/src
python new_detection_method.py -d /path/to/input/text/files/ -i /path/to/input/information/ -o /path/to/output/folder/ -O /path/to/tsv.tsv
```
This creates output_file.txt in /path/to/output/folder/ with the detected suggestions.

## Procedure Description

##### Steps:
1. Parse annotation information in route specified with -i option.
2. Find text spans in -d that are in -i. Assign a code to them.
3. Write TSV file in -o

##### Arguments:
+ **Input**: 
	+ -d option: text files.
	+ -i option: annotation information: TSV with 3 columns: code, span and label.

+ **Output**: 
	+ -o option. Output folder where output file will be created.
	+ -O option. TSV file with the information contained in the parsed files from -i option.


##### To execute it: 
```
cd detect_annotations/src
python new_detection_method.py -i ../toy_data/information.tsv -d ../toy_data/ -o ../../ -O ../../here.tsv
```
This creates output_file.txt in ../../.


## Built With

* [Python3.7](https://www.anaconda.com/distribution/)

## Authors

* **Antonio Miranda** - antonio.miranda@bsc.es
