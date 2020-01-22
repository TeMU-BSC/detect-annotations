#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 15:45:05 2019

@author: antonio
"""

#import sys
#sys.path.insert(1, '.')

import itertools
import os
import time
from utils.app_specific_utils import (parse_ann, format_ann_info,
                                      format_text_info, modify_copied_files,
                                      store_prediction, parse_tsv,
                                      check_surroundings, remove_redundant_suggestions)

from utils.general_utils import (argparser, Flatten, copy_dir_structure, 
                                 copy_all_files)   
                            

def find_new_annotations(datapath, min_upper, file2annot_processed, file2annot,
                         annot2label, annot2annot_processed):
    start = time.time()
    
    annotations_not_in_ann = {}
    c = 0
    for root, dirs, files in os.walk(datapath):
        for filename in files:
            if filename[-3:] == 'txt': # get only txt files
                print(filename)
                
                #### 0. Initialize, etc. ####
                new_annotations = []
                pos_matrix = []
                filename_ann = filename[0:-3]+ 'ann'
                 
                #### 1. Open txt file ####
                txt = open(os.path.join(root,filename)).read()
        
                #### 2. Format text information ####
                words_final, words_processed2pos = format_text_info(txt, min_upper)
                
                #### 3. Intersection ####
                # Find words within annotations of OTHER files
                annot_processed_other_files = list(dict(filter(lambda elem: elem[0] != filename_ann, 
                                                           file2annot_processed.items())).values())
                
                # Flatten results and get set of it
                annotations_final = set(Flatten(annot_processed_other_files))
                
                # Generate candidates
                words_in_annots = words_final.intersection(annotations_final)
                    
                #### 4. For every token of the intersection, get all original 
                #### annotations associated to it and all matches in text.
                #### Then, check surroundings of all those matches to check if any
                #### of the original annotations is in the text ####
                for match in words_in_annots:

                    # Get annotations where this token is present
                    original_annotations = [k for k,v in annot2annot_processed.items() if match in v]
                    # Get text locations where this token is present
                    match_text_locations = words_processed2pos[match]
                     
                    # For every original annotation where this token is present:
                    for original_annot in original_annotations:
                        original_label = annot2label[original_annot]
                        original_text_locations = words_processed2pos[match]
                        n_chars = len(original_annot)
                        n_words = len(original_annot.split())
                        
                        if len(original_annot.split()) > 1:
                            # For every match of the token in text, check its 
                            # surroundings and generate predictions
                            for span in match_text_locations:
                                (new_annotations, 
                                 pos_matrix) = check_surroundings(txt, span, 
                                                                  original_annot,
                                                                  n_chars, n_words,
                                                                  original_label,
                                                                  new_annotations,
                                                                  pos_matrix, min_upper)
                                
                        # If original_annotation is just the token, no need to 
                        # check the surroundings
                        elif len(original_annot.split()) == 1:
                            for span in original_text_locations:
                                # Check span is surrounded by spaces or punctuation signs &
                                # span is not contained in a previously stored prediction
                                if (((txt[span[0]-1].isalnum() == False) &
                                     (txt[span[1]].isalnum() == False)) &
                                    (not any([(item[0]<=span[0]) & (span[1]<=item[1]) 
                                              for item in pos_matrix]))):
                                    
                                    # STORE PREDICTION and eliminate old predictions
                                    # contained in the new one.
                                    (new_annotations, 
                                     pos_matrix) = store_prediction(pos_matrix, 
                                                                    new_annotations,
                                                                    span[0], span[1], 
                                                                    original_label,
                                                                    original_annot,
                                                                    txt)

                        
                ## 4. Remove duplicates ##
                new_annotations.sort()
                new_annots_no_duplicates = list(k for k,_ in itertools.groupby(new_annotations))
                
                ## 5. Check new annotations are not already annotated in their own ann
                if filename_ann not in file2annot.keys():
                    final_new_annots = new_annots_no_duplicates
                else:
                    annots_in_ann = file2annot[filename_ann]
                    final_new_annots = []
                    for new_annot in new_annots_no_duplicates:
                        new_annot_word = new_annot[0]
                        if any([new_annot_word in x for x in annots_in_ann]) == False:
                            final_new_annots.append(new_annot)
                            
                # Final appends
                c = c + len(final_new_annots)
                annotations_not_in_ann[filename] = final_new_annots
                
    total_t = time.time() - start
    
    return total_t, annotations_not_in_ann, c

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
    file2annot, file2annot_processed, annot2label, annot2annot_processed = format_ann_info(df_annot,
                                                                                           min_upper)
    
    
    ######## FIND MATCHES IN TEXT ########
    print('\n\nFinding new annotations...\n\n')
    total_t, annotations_not_in_ann, c = find_new_annotations(datapath, min_upper, 
                                                              file2annot_processed, file2annot,
                                                              annot2label, annot2annot_processed)
    
    print('Elapsed time: {}s'.format(round(total_t, 3)))
    print('Number of suggested annotations: {}'.format(c))
    #print(annotations_not_in_ann)
       
    
    ######### WRITE FILES #########   
    print('\n\nWriting new brat files...\n\n')
    # Create directory structure  
    print(datapath)
    print(output_path_new_files)          
    copy_dir_structure(datapath, output_path_new_files)
    
    # Copy all files           
    copy_all_files(datapath, output_path_new_files)
    
    # Modify annotated files
    modify_copied_files(annotations_not_in_ann, output_path_new_files)
    
    
    ######## REMOVE REDUNDANT SUGGESTIONS ########
    print("\n\nRemoving redundant suggestions...\n\n")
    remove_redundant_suggestions(output_path_new_files)
    
    print('\n\nFINISHED!')
