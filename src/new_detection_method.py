#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 15:45:05 2019

@author: antonio
"""

from utils.app_specific_utils import modify_copied_files,\
    remove_redundant_suggestions,format_ann_info
from utils.parse import parse_tsv, parse_ann
from utils.general_utils import argparser, copy_dir_structure, copy_all_files, \
    remove_accents
from detect_annotations import detect_annots, detect_annots_dummy
import os

if __name__ == '__main__':
    
    ######## Set up some variables########
    min_upper = 5 # minimum number of characters a string must have to lowercase it
    labels_to_ignore = ['_REJ_PROFESION', '_REJ_ACTIVIDAD','_REJ_SITUACION_LABORAL','_SUG_PROFESION', '_SUG_ACTIVIDAD','_SUG_SITUACION_LABORAL']
    ignore_annots = []
    
    ######## Parse command line arguments ########   
    print('\n\nParsing script arguments...\n\n')
    datapath, information_path, out_path, to_ignore, with_notes = argparser()

    ######## Parse INFORMATION ########    
    # Get DataFrame
    print('\n\nObtaining original annotations...\n\n')
    if information_path.split('.')[-1] == 'tsv':
        df_annot = parse_tsv(information_path)
    else:
        df_annot = parse_ann(information_path, labels_to_ignore, with_notes)
    
    # Remove annots
    if bool(to_ignore) == True:
        span_new = df_annot['span']
        span_new = span_new.apply(lambda x: remove_accents(x).lower())
        df_annot = df_annot.drop(df_annot[span_new.isin(ignore_annots)].index)
        
    ######## FORMAT ANN INFORMATION #########
    print('\n\nFormatting original annotations...\n\n')
    file2annot, file2annot_processed, annot2label, annot2annot_processed, \
        annot2code = format_ann_info(df_annot, min_upper, with_notes)
    
    
    ######## FIND MATCHES IN TEXT ########
    print('\n\nFinding new annotations...\n\n')
    print(datapath)
    '''total_t, detected_annots, c = \
        detect_annots_dummy(datapath, min_upper, annot2code, file2annot_processed,
        file2annot, annot2label, annot2annot_processed, with_notes)'''
    
    total_t, detected_annots, c = \
        detect_annots(datapath, min_upper, annot2code, file2annot_processed, 
                      file2annot, annot2label, annot2annot_processed, with_notes)
   
    print('Elapsed time: {}s'.format(round(total_t, 3)))
    print('Number of suggested annotations: {}'.format(c))

    # Remove annotations with \n inside them
    detected_annots_clean = {}
    for k,v in detected_annots.items():
        val = []
        for annot in v:
            if '\n' in annot[0]:
                continue
            val.append(annot)
        detected_annots_clean[k] = val
                       
    
    ######### WRITE FILES #########   
    print('\n\nWriting new brat files...\n\n')
    # Create directory structure  
    print(datapath)
    print(out_path)          
    copy_dir_structure(datapath, out_path)
    
    # Copy all files           
    copy_all_files(datapath, out_path)
    
    # Modify annotated files
    modify_copied_files(detected_annots_clean, out_path, with_notes)
    
    
    ######## REMOVE REDUNDANT SUGGESTIONS ########
    print("\n\nRemoving redundant suggestions...\n\n")
    removed_suggestions = remove_redundant_suggestions(out_path)
    print('Final number of suggested annotations: {}'.format(c-removed_suggestions))
    
    print('\n\nFINISHED!')
