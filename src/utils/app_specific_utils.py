#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 15 18:24:28 2020

@author: antonio
"""

import pandas as pd
import os
import time
import string
from spacy.lang.es import STOP_WORDS
from utils.general_utils import remove_accents, adjacent_combs, strip_punct, normalize_str
import re


def tokenize_span(text, n_words):
    '''
    DESCRIPTION: obtain all token combinations in a text and information 
    about the position of every token combination in the original text.
    
    Parameters
    ----------
    text: string
    n_words: int 
        It is the maximum number of tokens I want in a token combination.

    Returns
    -------
    token_span2id: python dict 
        It relates every token combination with an ID.
    id2token_span_pos: python dict
        It relates every token combination (identified by an ID) with its 
        position in the text.
    token_spans: list
        list of token combinations
    '''
    
    # Split text into tokens (words), obtain their position and the previous token.
    tokens2pos = {}
    m_last = ''
    for m in re.finditer(r'\S+', text):
        if all([i in string.punctuation for i in m.group()])==False:
            exit_bool = 0
            
            # remove final and initial punctuation
            m_end, m_start, m_group, exit_bool = strip_punct(m.end(), m.start(),
                                                             m.group(), exit_bool)
                
            # fill dictionary
            if m_group in tokens2pos.keys():
                tokens2pos[m_group].append([m_start, m_end, m_last])
            else:
                tokens2pos[m_group] = [[m_start, m_end, m_last]]
            m_last = m_group
        
    # Obtain token combinations
    id2token_span, id2token_span_pos, token_spans = adjacent_combs(text, 
                                                                   tokens2pos,
                                                                   n_words)
    
    # Reverse dict (no problem, keys and values are unique)
    token_span2id = {' '.join(v): k for k, v in id2token_span.items()}
    
    return token_span2id, id2token_span_pos, token_spans
    
def normalize_tokens(token_spans, min_upper):
    '''
    DESCRIPTION: normalize tokens: lowercase, remove extra whitespaces, 
    remove punctuation and remove accents.
    
    Parameters
    ----------
    token_spans: list
    min_upper: int. S
        It specifies the minimum number of characters of a word to lowercase
        it (to prevent mistakes with acronyms).

    Returns
    -------
    token_span_processed2token_span: python dict 
        It relates the normalized token combinations with the original unnormalized ones.
    '''
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
    token_span_processed2token_span = dict((remove_accents(k), v) for k,v in token_span_punc2token_span.items())
    
    return token_span_processed2token_span

def modify_copied_files(annotations_not_in_ann, output_path_new_files):
    '''
    DESCRIPTION: add suggestions (newly discovered annotations) to ann files.
    
    Parameters
    ----------
    annotations_not_in_ann: python dict 
        It has new annotations and the file they belong to. 
        {filename: [annotation1, annotatio2, ]}
    output_path_new_files: str. 
        Path to files.
    '''
    files_new_annot = list(annotations_not_in_ann.keys())
    
    for root, dirs, files in os.walk(output_path_new_files):
        for filename in files:
            if filename in files_new_annot:
                if filename[-3:] == 'txt':       
                    filename_ann = filename[0:-3]+ 'ann'
                    #print(filename)
                    # 1. Open .ann file & get highest mark
                    with open(os.path.join(root,filename_ann),"r") as file:
                        lines = file.readlines()
                        if lines:
                            # Get marks
                            marks = list(map(lambda x: int(x.split('\t')[0][1:]),
                                             filter(lambda x: x[0] == 'T', lines)))
                        
                            # 2. Get highest mark
                            mark = max(marks)
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
                            file.write('#' + str(mark) + '\t' + 'AnnotatorNotes' +
                                       ' T' + str(mark) + '\t' + a[4] + '\n') 
                            

def parse_ann(datapath, output_path):
    '''
    DESCRIPTION: parse information in .ann files.
    
    Parameters
    ----------
    datapath: str. 
        Route to the folder where the files are. 
    output_path: str. 
        Path to output TSV where information will be stored.
           
    Returns
    -------
    df: pandas DataFrame 
        It has information from ann files. Columns: 'annotator', 'bunch',
        'filename', 'mark', 'label', 'offset1', 'offset2', 'span', 'code'
    filenames: list 
        list of filenames
    '''
    start = time.time()
    info = []
    c = 0
    ## Iterate over the files and parse them
    filenames = []
    for root, dirs, files in os.walk(datapath):
         for filename in files:
             if filename[-3:] == 'ann': # get only ann files
                 #print(os.path.join(root,filename))
                 
                 f = open(os.path.join(root,filename)).readlines()
                 filenames.append(filename)
                 # Get annotator and bunch
                 bunch = root.split('/')[-1]
                 annotator = root.split('/')[-2][-1]
                 
                 # Parse .ann file
                 mark2code = {}
                 for line in f:
                     if line[0] == '#':
                         line_split = line.split('\t')
                         mark2code[line_split[1].split(' ')[1]] = line_split[2].strip()
                         
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
                             c = c +1
                             pass
                         else:
                             if mark in mark2code.keys():
                                 code = mark2code[mark]
                                 info.append([annotator, bunch, filename,
                                                  mark, label, offset[0], offset[-1],
                                                  span.strip(string.punctuation), code])
                     
    end = time.time()
    print("Elapsed time: " + str(round(end-start, 2)) + 's')
    
    # Save parsed .ann files
    df = pd.DataFrame(info, columns=['annotator', 'bunch', 'filename', 'mark',
                                     'label', 'offset1', 'offset2', 'span', 'code'])
    df.to_csv(output_path, sep='\t',index=False)
    
    print('Number of discontinuous annotations: {}'.format(c))
    return df, filenames

def parse_tsv(input_path_old_files):
    '''
    DESCRIPTION: Get information from ann that was already stored in a TSV file.
    
    Parameters
    ----------
    input_path_old_files: string
        path to TSV file with columns: ['annotator', 'bunch', 'filename', 
        'mark','label', 'offset1', 'offset2', 'span', 'code']
        Additionally, we can also have the path to a 3 column TSV: ['code', 'label', 'span']
    
    Returns
    -------
    df_annot: pandas DataFrame
        It has 4 columns: 'filename', 'label', 'code', 'span'.
    '''
    df_annot = pd.read_csv(input_path_old_files, sep='\t', header=None)
    if len(df_annot.columns) == 8:
        df_annot.columns=['annotator', 'bunch', 'filename', 'mark',
                      'label', 'offset1', 'offset2', 'span', 'code']
    else:
        df_annot.columns = ['code', 'span', 'label']
        #df_annot['label'] = 'MORFOLOGIA_NEOPLASIA'
        df_annot['filename']  ='xx'
    return df_annot

def format_ann_info(df_annot, min_upper):
    '''
    DESCRIPTION: Build useful Python dicts from DataFrame with info from TSV file
    
    Parameters
    ----------
    df_annot: pandas DataFrame 
        With 4 columns: 'filename', 'label', 'code', 'span'
    min_upper: int. 
        It specifies the minimum number of characters of a word to lowercase 
        it (to prevent mistakes with acronyms).
    
    Returns
    -------
    file2annot: python dict
    file2annot_processed: python dict
    annot2label: python dict
        It has every unmodified annotation and its label.
    annot2annot_processed: python dict 
        It has every unmodified annotation and the words it has normalized.
    '''
    # Build useful Python dicts from DataFrame with info from .ann files
    file2annot = {}
    for filename in list(df_annot.filename):
        file2annot[filename] = list(df_annot[df_annot['filename'] == filename].span)
        
    set_annotations = set(df_annot.span)
    
    annot2label = dict(zip(df_annot.span,df_annot.label))
    
    annot2code = df_annot.groupby('span')['code'].apply(lambda x: x.tolist()).to_dict()
    
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
    annot2annot_processed = annot2annot_lower.copy()
    for k, v in annot2annot_lower.items():
        annot2annot_processed[k] = list(map(lambda x: remove_accents(x), v))
    
    # file2unaccented annotations
    file2annot_processed = {}
    for (k,v) in file2annot.items():
        aux = list(map(lambda x:annot2annot_processed[x], v))
        file2annot_processed[k] = aux

    return file2annot, file2annot_processed, annot2label, annot2annot_processed, annot2code


def format_text_info(txt, min_upper):
    '''
    DESCRIPTION: 
    1. Obtain list of words of interest in text (no STPW and longer than 1 character)
    2. Obtain dictionary with words of interest and their position in the 
    original text. Words of interest are normalized: lowercased and removed 
    accents.
    
    Parameters
    ----------
    txt: str 
        contains the text to format.
    min_upper: int. 
        Specifies the minimum number of characters of a word to lowercase it
        (to prevent mistakes with acronyms).
    
    Returns
    -------
    words_processed2pos: dictionary
        It relates the word normalzied (trimmed, removed stpw, lowercased, 
        removed accents) and its position in the original text.
    words_final: set
            set of words in text.
    '''
    
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
    words_processed2pos = dict((remove_accents(k.lower()), v) if len(k) > min_upper else 
                                (k,v) for k,v in words2pos.items())
    
    # Set of transformed words
    words_final = set(words_processed2pos)
    
    return words_final, words_processed2pos

def store_prediction(pos_matrix, predictions, off0, off1, original_label, 
                     original_annot, txt, code):
                                        
    # 1. Eliminate old annotations if the new one contains them
    (pos_matrix, 
     predictions) = eliminate_contained_annots(pos_matrix, predictions, off0, off1)
    
    # 2. STORE NEW PREDICTION
    predictions.append([txt[off0:off1], off0, off1, original_label, code])   
    pos_matrix.append([off0, off1])
        
    return predictions, pos_matrix


def eliminate_contained_annots(pos_matrix, new_annotations, off0, off1):
    '''
    DESCRIPTION: function to be used when a new annotation is found. 
              It check whether this new annotation contains in it an already 
              discovered annotation. In that case, the old annotation is 
              redundant, since the new one contains it. Then, the function
              removes the old annotation.
    '''
    to_eliminate = [pos for item, pos in zip(pos_matrix, range(0, len(new_annotations))) 
                    if (off0<=item[0]) & (item[1]<=off1)]
    new_annotations = [item for item, pos in zip(new_annotations, range(0, len(new_annotations)))
                       if pos not in to_eliminate]
    pos_matrix = [item for item in pos_matrix if not (off0<=item[0]) & (item[1]<=off1)]
    
    return pos_matrix, new_annotations


def check_surroundings(txt, span, original_annot, n_chars, n_words, original_label,
                       predictions, pos_matrix, min_upper, code):
    '''
    DESCRIPTION: explore the surroundings of the match.
              Do not care about extra whitespaces or punctuation signs in 
              the middle of the annotation.
    '''
    
    ## 1. Get normalized surroundings ##
    large_span = txt[max(0, span[0]-n_chars):min(span[1]+n_chars, len(txt))]

    # remove half-catched words
    try:
        first_space = re.search('( |\n)', large_span).span()[1]
    except: 
        first_space = 0
    try:
        last_space = (len(large_span) - re.search('( |\n)', large_span[::-1]).span()[0])
    except:
        last_space = len(large_span)
    large_span_reg = large_span[first_space:last_space]
    
    # Tokenize text span 
    token_span2id, id2token_span_pos, token_spans = tokenize_span(large_span_reg,
                                                                  n_words)
    # Normalize
    original_annotation_processed = normalize_str(original_annot, min_upper)
    token_span_processed2token_span = normalize_tokens(token_spans, min_upper)
    
    ## 2. Match ##
    try:
        res = token_span_processed2token_span[original_annotation_processed]
        id_ = token_span2id[res]
        pos = id2token_span_pos[id_]
        off0 = (pos[0] + first_space + max(0, span[0]-n_chars))
        off1 = (pos[1] + first_space + max(0, span[0]-n_chars))
        
        # Check new annotation is not contained in a previously stored new annotation
        if not any([(item[0]<=off0) & (off1<= item[1]) for item in pos_matrix]):
            # STORE PREDICTION and eliminate old predictions contained in the new one.
            predictions, pos_matrix = store_prediction(pos_matrix, predictions,
                                                       off0, off1, 
                                                       original_label,
                                                       original_annot, txt, code)
    except: 
        pass
    
    return predictions, pos_matrix

def remove_redundant_suggestions(datapath):
    '''
    DESCRIPTION: 
    Parameters
    ----------
    datapath : TYPE
        DESCRIPTION.

    Returns
    -------
    c : TYPE
        DESCRIPTION.

    '''
    c = 0
    for root, dirs, files in os.walk(datapath):
        for filename in files:
            if filename[-3:] == 'ann': # get only ann files
                f = open(os.path.join(root,filename)).readlines()
                #print(os.path.join(root, filename))
                offsets = []
                to_delete = []
                
                # 1. Get position of confirmed annotations
                for line in f:
                    if (line[0] == 'T') & (line.split('\t')[1][0:5] != '_SUG_'):
                        splitted = line.split('\t')
                        label_offset = splitted[1].split(' ')
                        if ';' not in label_offset[1:][1]: # Do not store discontinuous annotations
                            offsets.append([int(label_offset[1:][0]), int(label_offset[1:][1])])
                            
                # 2.1 Get position of suggestions.
                # 2.2 Check suggestions are not contained in any confirmed annotation
                for line in f:
                    if (line[0] == 'T') & (line.split('\t')[1][0:5] == '_SUG_'):
                        splitted = line.split('\t')
                        label_offset = splitted[1].split(' ')
                        new_offset = [int(label_offset[1:][0]), int(label_offset[1:][1])]
                        if any(map(lambda x: (x[0] <= new_offset[0]) & (x[1] >= new_offset[1]), offsets)):
                            to_delete.append(splitted[0])
                            c = c +1
                                
                # 3. Re-write ann without suggestions that were contained in a
                # confirmed annotation
                with open(os.path.join(root,filename), 'w') as fout:
                    for line in f:
                        if line.split('\t')[0] not in to_delete:
                            fout.write(line)
    return c