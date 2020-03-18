#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 15:45:05 2019

@author: antonio
"""

from utils.app_specific_utils import (parse_ann,parse_tsv,modify_copied_files,
                                      remove_redundant_suggestions,format_ann_info)

from utils.general_utils import argparser, copy_dir_structure, copy_all_files
                            
from detect_annotations import detect_annots, detect_annots_dummy


if __name__ == '__main__':
    
    ######## Set up some variables########
    min_upper = 5 # minimum number of characters a string must have to lowercase it
    valid_labels = ['MORFOLOGIA_NEOPLASIA']
    ignore_annots = ['marcador tumoral', 'marcadores tumorales', 
                     'marcador tumorales', 'marcadores tumoral']
    
    ######## Parse command line arguments ########   
    print('\n\nParsing script arguments...\n\n')
    datapath, information_path, out_path, out_path_df = argparser()
    
    ######## GET ANN INFORMATION ########    
    # Get DataFrame
    print('\n\nObtaining original annotations...\n\n')
    if information_path.split('.')[-1] == 'tsv':
        df_annot = parse_tsv(information_path)
    else:
        df_annot, _ = parse_ann(information_path, out_path_df, valid_labels)
    
    
    ######## FORMAT ANN INFORMATION #########
    print('\n\nFormatting original annotations...\n\n')
    (file2annot, file2annot_processed, annot2label, 
     annot2annot_processed, annot2code) = format_ann_info(df_annot, min_upper)
    
    
    ######## FIND MATCHES IN TEXT ########
    print('\n\nFinding new annotations...\n\n')
    print(datapath)
    '''total_t, detected_annots, c = detect_annots(datapath, min_upper, annot2code,
                                                file2annot_processed, file2annot,
                                                annot2label, annot2annot_processed)'''
    
    total_t, detected_annots, c = detect_annots(datapath, min_upper, annot2code,
                                                file2annot_processed, file2annot,
                                                annot2label, annot2annot_processed)
    print(detected_annots)
    # Remove annotations
    for element in ignore_annots:
        detected_annots = {k: [x for x in v if element != x[0]] for k, v in detected_annots.items()}
    
    print('Elapsed time: {}s'.format(round(total_t, 3)))
    print('Number of suggested annotations: {}'.format(c))
    #print(detected_annots)
       
    
    ######### WRITE FILES #########   
    print('\n\nWriting new brat files...\n\n')
    # Create directory structure  
    print(datapath)
    print(out_path)          
    copy_dir_structure(datapath, out_path)
    
    # Copy all files           
    copy_all_files(datapath, out_path)
    
    # Modify annotated files
    modify_copied_files(detected_annots, out_path)
    
    
    ######## REMOVE REDUNDANT SUGGESTIONS ########
    print("\n\nRemoving redundant suggestions...\n\n")
    removed_suggestions = remove_redundant_suggestions(out_path)
    print('Final number of suggested annotations: {}'.format(c-removed_suggestions))
    
    print('\n\nFINISHED!')
