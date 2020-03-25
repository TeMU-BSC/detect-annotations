#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 25 09:40:48 2020

@author: antonio
"""
import itertools
import re
import os
import time
from utils.app_specific_utils import (format_text_info, store_prediction,
                                      check_surroundings)
from utils.general_utils import Flatten


def detect_annots(datapath, min_upper, annot2code, file2annot_processed,
                         file2annot, annot2label, annot2annot_processed):
    '''
    
    Parameters
    ----------
    datapath : TYPE
        DESCRIPTION.
    min_upper : TYPE
        DESCRIPTION.
    annot2code : TYPE
        DESCRIPTION.
    file2annot_processed : TYPE
        DESCRIPTION.
    file2annot : TYPE
        DESCRIPTION.
    annot2label : TYPE
        DESCRIPTION.
    annot2annot_processed : TYPE
        DESCRIPTION.

    Returns
    -------
    total_t : float
        Elapsed time
    annotations_not_in_ann : dict
        key= string with filename.txt (ex: 'cc_onco837.txt').
        Value = list of annotations (ex: [['Carcinoma microcítico',2690,2711,'MORFOLOGIA_NEOPLASIA','8041/3'],
                                          ['LH', 2618, 2620, '_REJ_MORFOLOGIA_NEOPLASIA', '9650/3']])
    c : int
        number of suggested annotations.

    '''
    start = time.time()
    
    annotations_not_in_ann = {}
    c = 0
    for root, dirs, files in os.walk(datapath):
        for filename in files:
            if filename[-3:] != 'txt':
                # get only txt files
                continue
            
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
                #print(len(original_annotations))
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
                        codes = annot2code[original_annot]
                        len_original = len(new_annotations)
                        for span in match_text_locations:
                            #print(new_annotations)
                            (new_annotations, 
                             pos_matrix) = check_surroundings(txt, span, 
                                                              original_annot,
                                                              n_chars, n_words,
                                                              original_label,
                                                              new_annotations,
                                                              pos_matrix, min_upper, codes)
                            if len(new_annotations) != len_original:
                                # condition to stop looking for the same code
                                # in more than one place
                                break
                            
                    # If original_annotation is just the token, no need to 
                    # check the surroundings
                    elif len(original_annot.split()) == 1:
                        len_original = len(new_annotations)
                        for span in original_text_locations:
                            # Check span is surrounded by spaces or punctuation signs &
                            # span is not contained in a previously stored prediction
                            if span[0] == 0:
                                cond_a = True
                            else:
                                cond_a = txt[span[0]-1].isalnum() == False
                            if span[1] == len(txt):
                                cond_b = True
                            else:
                                cond_b = txt[span[1]].isalnum() == False

                                
                            if ((cond_a & cond_b) &
                                (not any([(item[0]<=span[0]) & (span[1]<=item[1]) 
                                          for item in pos_matrix]))):
                                
                                # STORE PREDICTION and eliminate old predictions
                                # contained in the new one.
                                codes = annot2code[original_annot]
                                (new_annotations, 
                                 pos_matrix) = store_prediction(pos_matrix, 
                                                                new_annotations,
                                                                span[0], span[1], 
                                                                original_label,
                                                                original_annot,
                                                                txt, codes)
                                if len(new_annotations) != len_original:
                                    # condition to stop looking for the same code
                                    # in more than one place
                                    break

                        
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
