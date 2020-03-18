#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 18 10:49:54 2020

@author: antonio
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 15 17:44:18 2020

@author: antonio
"""

import itertools
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
    datapath : str
        Path to files.
    min_upper : int
        Minimum number of characters to consider casing as non-relevant.
    annot2code : dict
        Python dictionary mapping annotations to their codes.
    file2annot_processed : dict
        Python dict mapping filenames to a list of their annotations processed
        (lowercase, no stopwords, tokenized).
    file2annot : dict
        Python dict mapping filenames to a list of their annotations.
    annot2label : dict
        Python dict mapping annotations to their labels.
    annot2annot_processed : dict
        Python dict mapping annotations to the annotations processed 
        (lowercase, no stopwords, tokenized).

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
            if filename[-3:] == 'txt': # get only txt files
                print(filename)
                
                #### 0. Initialize, etc. ####
                new_annotations = []
                pos_matrix = []
                filename_ann = filename[0:-3]+ 'ann'
                 
                #### 1. Open txt file ####
                txt = open(os.path.join(root,filename)).read()
        
                #### 2. Format text information ####
                words_txt, words_processed2pos = format_text_info(txt, min_upper)
                
                #### 3. Intersection ####
                # Find words within annotations of OTHER files
                annots_other_files = dict(filter(lambda elem: elem[0] != filename_ann, 
                                                 file2annot_processed.items()))
                
                # Flatten results and get set of it
                words_annots = set(Flatten(list(annots_other_files.values())))
                
                # Generate candidates
                words_common = words_txt.intersection(words_annots)
                    
                #### 4. For every token of the intersection, get all original 
                #### annotations associated to it and all matches in text.
                #### Then, check surroundings of all those matches to check if any
                #### of the original annotations is in the text ####
                for match in words_common:

                    # Get annotations where this token is present
                    original_annotations = set([k for k,v in annot2annot_processed.items() if match in v])
                    # Get text locations where this token is present
                    match_text_locations = words_processed2pos[match]
                     
                    # For every original annotation where this token is present:
                    for original_annot in original_annotations:
                        original_label = annot2label[original_annot]
                        original_text_locations = words_processed2pos[match]
                        code = annot2code[original_annot][0]
                        n_chars = len(original_annot)
                        n_words = len(original_annot.split())
                        
                        if txt.find(original_annot.strip()) > -1:
                            pos0 = txt.find(original_annot.strip())
                            pos1 = (txt.find(original_annot.strip()) +
                                    len(original_annot.strip()))
                            
                            new_annotations.append([original_annot.strip(),
                                                    pos0, pos1, original_label,
                                                    code])
                            
                        
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
