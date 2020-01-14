#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 15:45:05 2019

@author: antonio
"""

# some_file.py
import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '.')

import string
from spacy.lang.es import STOP_WORDS
import re
import unicodedata
import itertools
import os
from shutil import copyfile
import time
from utils.parse_ann_for_detect_new_annotations import parse_ann
import argparse


def Flatten(ul):
    fl = []
    for i in ul:
        if type(i) is list:
            fl += Flatten(i)
        else:
            fl += [i]
    return fl


def copy_dir_structure(input_path_old_files, output_path_new_files):
    for dirpath, dirnames, filenames in os.walk(input_path_old_files):
        print(dirpath[len(input_path_old_files):])
        structure = os.path.join(output_path_new_files, 
                                 dirpath[len(input_path_old_files):])
        if not os.path.isdir(structure):
            print(structure)
            os.mkdir(structure)
        else:
            print("Folder does already exist!")
            
def copy_all_files(input_path_old_files, output_path_new_files):
    for root, dirs, files in os.walk(input_path_old_files):
        for filename in files:
            copyfile(os.path.join(root,filename), 
                     os.path.join(output_path_new_files,
                                  root[len(input_path_old_files):],
                                  filename))
            
def modify_copied_files(annotations_not_in_ann, output_path_new_files):
    files_new_annot = list(annotations_not_in_ann.keys())
    
    for root, dirs, files in os.walk(output_path_new_files):
        for filename in files:
            if filename in files_new_annot:
                if filename[-3:] == 'txt':       
                    filename_ann = filename[0:-3]+ 'ann'
                    #print(filename)
                    # 1. Open .ann file & get last line
                    with open(os.path.join(root,filename_ann),"r") as file:
                        lines = file.readlines()
                        if lines:
                            last_line = lines[-1]
                            c = 0
                            while last_line[0] != 'T':
                                c = c + 1
                                last_line = lines[-1 - c]
                        
                            # 2. Get last mark
                            mark = int(last_line.split('\t')[0][1:])
                        else:
                            # 2. Get last mark
                            mark = 0
                    
                    # 3. Write new annotations
                    new_annotations = annotations_not_in_ann[filename]
                    with open(os.path.join(root,filename_ann),"a") as file:
                        for a in new_annotations:
                            mark = mark + 1
                            file.write('T' + str(mark) + '\t' + '_SUG_' +  a[3] + 
                                       ' ' + str(a[1]) + ' ' + str(a[2]) + 
                                       '\t' + a[0] + '\n')
                            print(os.path.join(root,filename_ann))
                            
                            
def remove_accents(data):
    return ''.join(x for x in unicodedata.normalize('NFKD', data) if x in string.printable)

def adjacent_combs(text, tokens2pos, n_words):
    tokens = []
    for m in re.finditer(r'\S+', text):
        if all([i in string.punctuation for i in m.group()])==False:
            tokens.append(m.group())
    #tokens = text.split()
    tokens_trim = list(map(lambda x: x.strip(string.punctuation), tokens))
    id2token_span = {}
    id2token_span_pos = {}
    count = 0
    
    for a in range(0, len(tokens_trim)+1):
        for b in range(a+1, min(a + 1 + n_words, len(tokens_trim)+1)):
            count = count + 1

            tokens_group = tokens_trim[a:b] # Extract token group
            tokens_group = list(filter(None, tokens_group)) # remove empty elements
            
            if tokens_group:
                
                # Extract previous token
                token_prev = '' 
                if a>0:
                    c = 1
                    token_prev = tokens_trim[a-c:a][0]
                    # If token_prev is an empty space, it may be because there
                    # where a double empty space in the original text
                    while (token_prev == '') & (a>1):
                        c = c+1
                        token_prev = tokens_trim[a-c:a][0]
                        
                    
                id2token_span[count] = tokens_group
                
                if len(tokens_group) == 1:
                    pos = list(filter(lambda x: x[2] == token_prev, tokens2pos[tokens_group[0]]))
                    beg_pos = pos[0][0]
                    end_pos = pos[0][1]
                else:
                    beg =  list(filter(lambda x: x[2] == token_prev, tokens2pos[tokens_group[0]]))
                    end = list(filter(lambda x: x[2] == tokens_group[-2], tokens2pos[tokens_group[-1]]))
                    beg_pos = beg[0][0]
                    end_pos = end[0][1]
                    
                id2token_span_pos[count] = (beg_pos, end_pos) 

    token_spans = list(map(lambda x: ' '.join(x), id2token_span.values()))
    
    return id2token_span, id2token_span_pos, token_spans

def strip_punct(m_end, m_start, m_group, exit_bool):
    if m_group[-1] in string.punctuation:
        m_end = m_end - 1
        m_group = m_group[0:-1]
        m_start = m_start
        exit_bool = 0
    elif m_group[0] in string.punctuation:
        m_end = m_end
        m_group = m_group[1:]
        m_start = m_start + 1
        exit_bool = 0
    else: 
        m_end = m_end
        m_group = m_group
        m_start = m_start
        exit_bool = 1
    if exit_bool == 0:
        m_end, m_start, m_group, exit_bool = strip_punct(m_end, m_start, m_group, exit_bool)
    return m_end, m_start, m_group, exit_bool

def normalization_span(text, n_words):
    tokens2pos = {}
    
    m_last = ''
    for m in re.finditer(r'\S+', text):
        if all([i in string.punctuation for i in m.group()])==False:
            m_end = m.end()
            m_group = m.group()
            m_start = m.start()
            exit_bool = 0
            
            # remove final and initial punctuation
            m_end, m_start, m_group, exit_bool = strip_punct(m_end, m_start, m_group, exit_bool)
                
            # fill dictionary
            if m_group in tokens2pos.keys():
                tokens2pos[m_group].append([m_start, m_end, m_last])
            else:
                tokens2pos[m_group] = [[m_start, m_end, m_last]]
            m_last = m_group
        
    id2token_span, id2token_span_pos, token_spans = adjacent_combs(text, 
                                                                   tokens2pos,
                                                                   n_words)
    token_span2token_span = dict(zip(token_spans, token_spans))
    
    # Lowercase
    token_span_lower2token_span = dict((k.lower(), v) if len(k) > min_upper else 
                                       (k,v) for k,v in token_span2token_span.items())

    # Remove whitespaces
    token_span_bs2token_span = dict((re.sub('\s+', ' ', k).strip(), v) for k,v 
                                    in token_span_lower2token_span.items())

    # Remove punctuation
    token_span_punc2token_span = dict((k.translate(str.maketrans('', '', string.punctuation)), v) for k,v in token_span_bs2token_span.items())
    
    # Remove accents
    token_span_unacc2token_span = dict((remove_accents(k), v) for k,v in token_span_punc2token_span.items())
    
    return token_span_unacc2token_span, id2token_span, id2token_span_pos

def normalization_annot(annot):
       
    # Remove whitespaces
    annot_bs = re.sub('\s+', ' ', annot).strip()

    # Remove punctuation
    annot_punct = annot_bs.translate(str.maketrans('', '', string.punctuation))
    
    # Remove accents
    annot_unacc = remove_accents(annot_punct)
    
    return annot_unacc


def format_ann_info(df_annot, min_upper):
    # Build useful Python dicts from DataFrame with info from .ann files
    file2annot = {}
    for filename in list(df_annot.filename):
        file2annot[filename] = list(df_annot[df_annot['filename'] == filename].span)
        
    set_annotations = set(df_annot.span)
    
    annot2label = dict(zip(df_annot.span,df_annot.label))
    
    annot2annot = dict(zip(set_annotations, set_annotations))
    
    # Split values: {'one': 'three two'} must be {'one': ['three', 'two']}   
    annot2annot_split = annot2annot.copy()
    annot2annot_split = dict((k, v.split()) for k,v in annot2annot_split.items())
    
    # Do not store stopwords or single-character words as values
    for k, v in annot2annot_split.items():
        annot2annot_split[k] = list(filter(lambda x: x not in STOP_WORDS, v))
    for k, v in annot2annot_split.items():
        annot2annot_split[k] = list(filter(lambda x: len(x) > 1, v))
    
    # Trim punctuation or multiple spaces
    annot2annot_trim = annot2annot.copy()
    for k, v in annot2annot_split.items():
        annot2annot_trim[k] = list(map(lambda x: x.strip(string.punctuation + ' '), v))
        
    # Lower case values
    annot2annot_lower = annot2annot_trim.copy()
    for k, v in annot2annot_trim.items():
        annot2annot_lower[k] = list(map(lambda x: x.lower() if len(x) > min_upper else x, v))
    
    # remove accents from annotations
    annot2annot_unacc = annot2annot_lower.copy()
    for k, v in annot2annot_lower.items():
        annot2annot_unacc[k] = list(map(lambda x: remove_accents(x), v))
    
    # file2unaccented annotations
    file2annot_unacc = {}
    for (k,v) in file2annot.items():
        aux = list(map(lambda x:annot2annot_unacc[x], v))
        file2annot_unacc[k] = aux

    return file2annot, file2annot_unacc, annot2label, annot2annot_unacc

def format_text_info(txt, min_upper):
    # Get individual words and their position in original txt
    words = txt.split()
    
    # Remove beginning and end punctuation and whitespaces. 
    words_no_punctuation = list(map(lambda x: x.strip(string.punctuation + ' '), words))
    
    # Remove stopwords and single-character words
    large_words = list(filter(lambda x: len(x) > 1, words_no_punctuation))
    words_no_stw = set(filter(lambda x: x.lower() not in STOP_WORDS, large_words))
    
    # Create dict with words and their positions in text
    words2pos = {}
    for word in words_no_stw:
        occurrences = list(re.finditer(re.escape(word), txt))
        if len(occurrences) == 0:
            print('ERROR: ORIGINAL WORD NOT FOUND IN ORIGINAL TEXT')
            print(word)
        pos = list(map(lambda x: x.span(), occurrences))
        words2pos[word] = pos
        
    # lowercase words and remove accents from words
    words_unacc2pos = dict((remove_accents(k.lower()), v) if len(k) > min_upper else 
                                (k,v) for k,v in words2pos.items())
    
    # Set of transformed words
    words_final = set(words_unacc2pos)
    
    return words_final, words_unacc2pos



def find_new_annotations(datapath, min_upper, file2annot_unacc, file2annot,
                         annot2label, annot2annot_unacc):
    start = time.time()
    
    annotations_not_in_ann = {}
    c = 0
    for root, dirs, files in os.walk(datapath):
        for filename in files:
            if filename[-3:] == 'txt': # get only txt files
                print(filename)
                # 0. Initialize, etc.
                new_annotations = []
                filename_ann = filename[0:-3]+ 'ann'
                 
                ## 1. Open txt file
                txt = open(os.path.join(root,filename)).read()
        
                ## 2. Format text information ##
                words_final, words_unacc2pos = format_text_info(txt, min_upper)
                
                ## 3. Matching ##
                # Find words within annotations of OTHER files
                annot_unacc_other_files = list(dict(filter(lambda elem: elem[0] != filename_ann, 
                                                           file2annot_unacc.items())).values())
                
                # Flatten results and get set of it
                annotations_final = set(Flatten(annot_unacc_other_files))
                
                # Matching words
                words_in_annots = words_final.intersection(annotations_final)
                    
                for match in words_in_annots:
                    original_annotations = []
                    for k,v in annot2annot_unacc.items():
                        if match in v:
                            original_annotations.append(k)
                     
                    match_text_locations = words_unacc2pos[match]
                    for original_annot in original_annotations:
                        original_label = annot2label[original_annot]
                        original_text_locations = words_unacc2pos[match]
                        n_chars = len(original_annot)
                        n_words = len(original_annot.split())
                        
                        # If original_annotation is just the match, append it to new annotations
                        if (len(original_annot.split()) == 1):
                            for span in original_text_locations:
                                # Filter out things like 'espesor' -> 'peso'
                                if ((txt[span[0]-1].isalnum() == False) & (txt[span[1]].isalnum()==False)):
                                    new_annotations.append([txt[span[0]:span[1]], 
                                                            span[0], span[1], original_label])
            
                        # Else, need to explore around the match in the text according to the
                        # surroundings of the annotation.
                        # Do not care if extra whitespaces or punctuation signs 
                        else:
                            for match_span in match_text_locations:
                                large_span = txt[max(0, match_span[0]-n_chars):min(match_span[1]+n_chars, len(txt))]
                                
                                # remove half-catched words
                                first_space = re.search('( |\n)', large_span).span()[1]
                                last_space = len(large_span) - re.search('( |\n)', large_span[::-1]).span()[0]
                                large_span_reg = large_span[first_space:last_space]
                                
                                # normalize
                                original_annotation_norm = normalization_annot(original_annot)
                                (token_span_unacc2token_span, id2token_span, 
                                 id2token_span_pos) = normalization_span(large_span_reg, n_words)
                                token_span2id = {' '.join(v): k for k, v in id2token_span.items()}
                                
                                # Match
                                try:
                                    res = token_span_unacc2token_span[original_annotation_norm]
                                    id_ = token_span2id[res]
                                    pos = id2token_span_pos[id_]
                                    off0 = pos[0] + first_space + max(0, match_span[0]-n_chars)
                                    off1 = pos[1] + first_space + max(0, match_span[0]-n_chars)
                                    new_annotations.append([txt[off0:off1], off0, 
                                                            off1, original_label])                                
                                except: 
                                    pass
                        
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


def argparser():
    parser = argparse.ArgumentParser(description='process user given parameters')
    parser.add_argument("-i", "--input-brat", required = True, dest = "datapath", 
                        help = "absolute path to original input brat files")
    parser.add_argument("-o", "--output-brat", required =  True, 
                        dest="output_path_new_files", 
                        help = "absolute path to output brat files")
    parser.add_argument("-O", "--output_tsv", required = True, dest = "output_path_df", 
                        help = "absolute path to output TSV")
    
    args = parser.parse_args()
    
    datapath = args.datapath
    input_path_old_files = datapath
    output_path_new_files = args.output_path_new_files
    output_path_df = args.output_path_df
    
    return datapath, input_path_old_files, output_path_new_files, output_path_df


###################################


if __name__ == '__main__':
    
    min_upper = 5 # minimum number of characters a string must have to lowercase it

    ######## Define paths ########
    '''
    datapath = '/home/antonio/Documents/Projects/Tasks/CodiEsp/data/codificacion/terminados_only_oncology/'
    output_path_new_files = '/home/antonio/Documents/Projects/Tasks/CodiEsp/data/codificacion/terminados_only_oncology_suggestions/'
    output_path_df = '/home/antonio/Documents/Projects/Tasks/CodiEsp/data/codificacion/terminados_only_oncology/annots.tsv'
    output_path_df = '/home/antonio/Documents/Projects/Tasks/CodiEsp/data/codificacion/terminados_only_oncology/annots_to_delete.tsv'

    path = '/home/antonio/Documents/Projects/NER/merge_snomed_and_annotations/'
    datapath = 'data/testing_data2/'
    output_path_df = '/docs/parsed_ann_files_testing.tsv'
    input_path_old_files = 'data/testing_data2/'
    output_path_new_files = 'output/testing_data2/'
    
    path = '/home/antonio/Documents/Projects/NER/merge_snomed_and_annotations/'
    datapath = 'data/NER_FINAL/FINAL'
    output_path_df = '/docs/parsed_ann_files_testing.tsv'
    input_path_old_files = 'data/NER_FINAL/'
    output_path_new_files = 'output/new_NER_FINAL/'
    '''
    
    print('\n\nParsing script arguments...\n\n')
    datapath, input_path_old_files, output_path_new_files, output_path_df = argparser()
      
    
    ######## GET ANN INFORMATION ########    
    # Get DataFrame
    print('\n\nObtaining original .ann annotations...\n\n')
    df_annot, filenames = parse_ann(datapath, output_path_df)
    
    
    ######## FORMAT ANN INFORMATION #########
    print('\n\nFormatting original .ann annotations...\n\n')
    file2annot, file2annot_unacc, annot2label, annot2annot_unacc = format_ann_info(df_annot, min_upper)
    
    
    ######## FIND MATCHES IN TEXT ########
    print('\n\nFinding new annotations...\n\n')
    total_t, annotations_not_in_ann, c = find_new_annotations(datapath, min_upper, 
                                                              file2annot_unacc, file2annot,
                                                              annot2label, annot2annot_unacc)
    
    print('Elapsed time: {}s'.format(round(total_t, 3)))
    print('Number of suggested annotations: {}'.format(c))
    #print(annotations_not_in_ann)
    
    
    ######### WRITE FILES #########   
    print('\n\nWriting new brat files...\n\n')
    # Create directory structure
    print(input_path_old_files)
    print(output_path_new_files)               
    copy_dir_structure(input_path_old_files, output_path_new_files)
    
    # Copy all files           
    copy_all_files(input_path_old_files, output_path_new_files)
    
    # Modify annotated files
    modify_copied_files(annotations_not_in_ann, output_path_new_files)
