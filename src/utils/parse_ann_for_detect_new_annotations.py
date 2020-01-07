#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  8 14:11:07 2019

@author: antonio
"""

import pandas as pd
import os
import time
import string


def parse_ann(datapath, output_path):
    start = time.time()
    info = []
    
    ## Iterate over the files and parse them
    filenames = []
    for root, dirs, files in os.walk(datapath):
         for filename in files:
             if filename[-3:] == 'ann': # get only ann files
                 
                 f = open(os.path.join(root,filename)).readlines()
                 filenames.append(filename)
                 # Get annotator and bunch
                 bunch = root.split('/')[-1]
                 annotator = root.split('/')[-2][-1]
                 
                 # Parse .ann file
                 for line in f:
                     if line[0] == 'T':
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
                         offset = label_offset[1:]
                         span = splitted[2].strip()
                         if len(offset)>2:
                             #print(filename)
                             #print(offset)
                             pass
                         else:
                             info.append([annotator, bunch, filename,
                                              mark, label, offset[0], offset[-1],
                                              span.strip(string.punctuation)])
                     #else:
                         #print(os.path.join(root + filename))
                         #print('COMMENT LINE')
                         #print(line)
                     
    # Remove first dummy row
    end = time.time()
    print("Elapsed time: " + str(round(end-start, 2)) + 's')
    
    # Save parsed .ann files
    df = pd.DataFrame(info, columns=['annotator', 'bunch', 'filename', 'mark',
                                     'label', 'offset1', 'offset2', 'span'])
    df.to_csv(output_path, sep='\t',index=False)
    return df, filenames
