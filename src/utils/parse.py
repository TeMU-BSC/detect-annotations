#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 15:25:28 2020

@author: antonio
"""
import time
import os
import pandas as pd
import string

def parse_ann(datapath, labels_to_ignore = [], with_notes=False):
    '''
    DESCRIPTION: parse information in .ann files.
    
    Parameters
    ----------
    datapath: str. 
        Route to the folder where the files are. 
           
    Returns
    -------
    df: pandas DataFrame 
        It has information from ann files. Columns: 'annotator', 'bunch',
        'filename', 'mark', 'label', 'offset1', 'offset2', 'span', 'code'
    '''
    start = time.time()
    info = []
    ## Iterate over the files and parse them
    filenames = []
    print(datapath)
    for root, dirs, files in os.walk(datapath):
        for filename in files:
            if filename[-3:] != 'ann':
                continue
            info = parse_one_ann(info, filenames, root, filename, labels_to_ignore,
                                  ignore_related=True, with_notes=with_notes)
             
    if with_notes == True:
        df = pd.DataFrame(info, columns=['annotator','bunch','filename','mark',
                                     'label','offset1','offset2','span','code'])
    else:
        df = pd.DataFrame(info, columns=['annotator','bunch','filename','mark',
                                     'label','offset1','offset2','span'])
    end = time.time()
    print("Elapsed time: " + str(round(end-start, 2)) + 's')
    
    return df

def parse_one_ann(info, filenames, root, filename, labels_to_ignore,
                  ignore_related=True, with_notes=False):
    
    f = open(os.path.join(root,filename)).readlines()
    filenames.append(filename)
    # Get annotator and bunch
    bunch = root.split('/')[-1]
    annotator = root.split('/')[-2][-1]

    # Parse .ann file
    if with_notes==True:
        mark2code = {}
        for line in f:
            if line[0] != '#':
                continue
            line_split = line.split('\t')
            mark2code[line_split[1].split(' ')[1]] = line_split[2].strip()
    
    for line in f:
        if line[0] != 'T':
            continue
        splitted = line.split('\t')
        if len(splitted)<3:
            print('Line with less than 3 tabular splits:')
            print(root + filename)
            print(line)
            print(splitted)
        if len(splitted)>3:
            print('Line with more than 3 tabular splits:')
            print(root + filename)
            print(line)
            print(splitted)
        mark = splitted[0]
        label_offset = splitted[1].split(' ')
        label = label_offset[0]
        # Only store labels I am interested in
        if label in labels_to_ignore:
            continue
        offset = label_offset[1:]
        span = splitted[2].strip('\n')
        if with_notes==False:
            info.append([annotator, bunch, filename,mark, label,
                         offset[0], offset[-1], 
                         span.strip('\n')])
            continue
        
        if mark in mark2code.keys():
            code = mark2code[mark]
        else:
            code = ''
        info.append([annotator, bunch, filename,mark, label,
                     offset[0], offset[-1], 
                     span.strip('\n'), code])
            
    return info

def parse_tsv(in_path):
    '''
    DESCRIPTION: Get information from ann that was already stored in a TSV file.
    
    Parameters
    ----------
    in_path: string
        path to TSV file with columns: ['annotator', 'bunch', 'filename', 
        'mark','label', 'offset1', 'offset2', 'span', 'code']
        Additionally, we can also have the path to a 3 column TSV: ['code', 'label', 'span']
    
    Returns
    -------
    df_annot: pandas DataFrame
        It has 4 columns: 'filename', 'label', 'code', 'span'.
    '''
    df_annot = pd.read_csv(in_path, sep='\t', header=None)
    if len(df_annot.columns) == 8:
        df_annot.columns=['annotator', 'bunch', 'filename', 'mark',
                      'label', 'offset1', 'offset2', 'span', 'code']
    else:
        df_annot.columns = ['code', 'span', 'label']
        #df_annot['label'] = 'MORFOLOGIA_NEOPLASIA'
        df_annot['filename']  ='xx'
    return df_annot
