# Detect new annotations in BRAT files based on annotated entities of other files.

Codes to detect new missed annotations in .ann files. Detected annotations are added to the .ann files with the _SUG_ prefix.

## Getting Started

Scripts written in Python 3.7, anaconda distribution Anaconda3-2019.07-Linux-x86_64.sh

### Prerequisites

You need to have installed python3 and its base libraries, plus:
+ pandas
+ datetime
+ os
+ time
+ re
+ shutil
+ numpy
+ string
+ unicodedata

### Installing

```
git clone <repo_url>
```

## Running the scripts

### Find possible missing annotations and create new .ann files where they are suggested

+ File: 
src/new_detection_method.py

Description: 
1/ Parse annotated .ann files in data folder. The code run in this step is in src/utils/parse_ann_for_detect_new_annotations.py
2/ Find if some entities have been annotated in some files, but not in others. Copy .txt and new .ann files in output folder with the detected annotations marked as _SUG_LABEL. 

Input: .ann and .txt files in input folder.

Output: copied and modified .ann files and .txt files in output folder. Also, a TSV file is created with the information contained in the parsed .ann files.

To execute it: 

```
cd detect_annotations/src
python new_detection_method.py -i /absolute/path/to/input/folder/ -o /absolute/path/to/output/folder/ -O /path/to/tsv.tsv
```

It takes absolute paths, but it should work with relative paths.



### Scripts within utils/
+ File:
src/utils/parse_ann_for_detect_new_annotations.py -> parses .ann files in data/

Input: .ann files in data/

Output: TSV file with information contained in the parsed .ann files.

## Built With

* [Python3.7](https://www.anaconda.com/distribution/)

## Authors

* **Antonio Miranda** - antonio.miranda@bsc.es
