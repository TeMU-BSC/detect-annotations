# Detect new annotations in Text files based on TSV with codes and spans.

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

```
cd detect_annotations/src
python new_detection_method.py -d /path/to/input/text/files/ -i /path/to/input/information/ -o /path/to/output/folder/ -O /path/to/tsv.tsv
```


## Procedure Description

##### Steps:
1. Parse annotation information in route specified with -i option.
2. Find text spans in -d that are in -i. Assign a code to them.
3. Write TSV file in -o

##### Arguments:
+ **Input**: 
	+ -d option: text files.
	+ -i option: annotation information (can be .ann and .txt files or a TSV with 3 columns: code, span and label).

+ **Output**: 
	+ -o option. Output folder where new TSV will be created. 
	+ -O option. TSV file with the information contained in the parsed files from -i option.


##### To execute it: 
```
cd detect_annotations/src
python new_detection_method.py -d /path/to/input/text/files/ -i /path/to/input/information/ -o /path/to/output/folder/ -O /path/to/tsv.tsv
```



## Built With

* [Python3.7](https://www.anaconda.com/distribution/)

## Authors

* **Antonio Miranda** - antonio.miranda@bsc.es
