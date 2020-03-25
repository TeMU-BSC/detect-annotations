#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 15:45:05 2019

@author: antonio
OUTPUT_TSV
"""

#import sys
#sys.path.insert(1, '.')

import os
from utils.app_specific_utils import (parse_ann, format_ann_info, parse_tsv)
from utils.general_utils import argparser   
from detect_annotations import detect_annots


###################################


if __name__ == '__main__':
    
    min_upper = 5 # minimum number of characters a string must have to lowercase it

    ######## Define paths ########   
    print('\n\nParsing script arguments...\n\n')
    datapath, input_path_old_files, output_path_new_files, output_path_df = argparser()
    
    ######## GET ANN INFORMATION ########    
    # Get DataFrame
    print('\n\nObtaining original annotations...\n\n')
    if input_path_old_files.split('.')[-1] == 'tsv':
        df_annot = parse_tsv(input_path_old_files)
    else:
        df_annot, _ = parse_ann(input_path_old_files, output_path_df)
    
    ######## FORMAT ANN INFORMATION #########
    print('\n\nFormatting original annotations...\n\n')
    (file2annot, file2annot_processed, annot2label, 
     annot2annot_processed, annot2code) = format_ann_info(df_annot, min_upper)
    
    ######## FIND MATCHES IN TEXT ########
    print('\n\nFinding new annotations...\n\n')
    total_t, annotations_not_in_ann, c = detect_annots(datapath, min_upper, annot2code,
                                                       file2annot_processed, file2annot,
                                                       annot2label, annot2annot_processed)
    
    # Remove annotations that are always rejected
    l = ['marcador tumoral', 'marcadores tumorales', 'marcador tumorales', 
         'marcadores tumoral']
    for element in l:
        annotations_not_in_ann = {k: [x for x in v if l != x[0]] for k, v in annotations_not_in_ann.items()}
    
    print('Elapsed time: {}s'.format(round(total_t, 3)))
    print('Number of suggested annotations: {}'.format(c))
    
    ######## REMOVE REDUNDANT SUGGESTIONS ########
    
    #print(annotations_not_in_ann)
    
    ######### WRITE OUTPUT ###########
    print('\n\nWriting output...\n\n')
    with open(os.path.join(output_path_new_files, 'output_file.txt'), 'w') as f:
        for k,v in annotations_not_in_ann.items():
            for val in v:
                f.write(k)
                f.write('\t')
                f.write(str(val[4]))
                f.write('\t')
                f.write(str(val[0]))
                f.write('\n')
    
    
        
    
    ######## REMOVE REDUNDANT SUGGESTIONS ########
    '''print("\n\nRemoving redundant suggestions...\n\n")
    removed_suggestions = remove_redundant_suggestions(output_path_new_files)
    print('Final number of suggested annotations: {}'.format(c-removed_suggestions))'''
    
    print('\n\nFINISHED!')
