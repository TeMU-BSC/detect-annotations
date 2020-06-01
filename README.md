# Detect new annotations in BRAT files based on annotated entities of other files.

Codes to detect missed annotations in .ann files. Detected annotations are added to the .ann files with the \_SUG\_ prefix.

## Getting Started

Scripts written in Python 3.7, anaconda distribution Anaconda3-2019.07-Linux-x86_64.sh

### Prerequisites

You need to have installed python3 and its base libraries, plus:
+ pandas
+ numpy

### Installing

```
git clone <repo_url>
pip install -r requirements.txt
```

## Running the scripts

```
cd detect_annotations/src
python new_detection_method.py -d /path/to/input/text/files/ -i /path/to/input/information/ -o /path/to/output/folder/ -ig bool -c bool
```


## Procedure Description

##### Steps:
1. Parse annotation information in route specified with -i option.
2. Find text spans in -d that were annotated in -i. Assign a code to them.
3. Copy .txt and new .ann files in output folder with the detected annotations marked as \_SUG\_LABEL. 
4. Remove duplicates.


##### Arguments:
+ **Input**: 
	+ -d option: .ann and .txt files without suggestions.
	+ -i option: annotation information (can be .ann and .txt files or a TSV with 3 columns: code, span and label).
	+ --ignore_annots option: whether to ignore a custom list of forbidden annotations (the list must be changed in the code, sorry...).
	+ --predict-codes option: whether we will predict the codes, or only the annotations.
+ **Output**: 
	+ -o option. Output folder where new .ann and .txt files will be created. 


##### To execute it: 
```
cd detect_annotations/src
python new_detection_method.py -i ../toy_data/ -d ../toy_data/ -o ../output/ -ig False -c True
```



## Built With

* [Python3.7](https://www.anaconda.com/distribution/)

## Authors

* **Antonio Miranda** - antonio.miranda@bsc.es
