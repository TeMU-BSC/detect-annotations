#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 15 18:24:28 2020

@author: antonio
"""

import pandas as pd
import os
import string
from spacy.lang.es import STOP_WORDS
import re
from utils.general_utils import (remove_accents, adjacent_combs, strip_punct, 
                                 tokenize, normalize_str)



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
            m_end, m_start, m_group, exit_bool = \
                strip_punct(m.end(), m.start(), m.group(), exit_bool)
                
            # fill dictionary
            if m_group in tokens2pos.keys():
                tokens2pos[m_group].append([m_start, m_end, m_last])
            else:
                tokens2pos[m_group] = [[m_start, m_end, m_last]]
            m_last = m_group
        
    # Obtain token combinations
    id2token_span, id2token_span_pos, token_spans = \
        adjacent_combs(text, tokens2pos, n_words)
    
    # Reverse dict (no problem, keys and values are unique)
    token_span2id = {' '.join(v): k for k, v in id2token_span.items()}
    
    return token_span2id, id2token_span_pos, token_spans
    
def normalize_tokens(tokens, min_upper):
    '''
    DESCRIPTION: normalize tokens: lowercase, remove extra whitespaces, 
    remove punctuation and remove accents.
    CAREFULL! I LOSE INFORMATION IF I HAVE TWO DIFFERENT TOKENS WHICH ARE
    NORMALIZED TO THE SAME STRING
    
    Parameters
    ----------
    tokens: list
    min_upper: int. S
        It specifies the minimum number of characters of a word to lowercase
        it (to prevent mistakes with acronyms).
    Returns
    -------
    token_processed2token: python dict 
        It relates the normalized tokens with the original unnormalized ones.
    '''
    token2token = dict(zip(tokens, tokens))
    
    # Lowercase
    token_lower2token = dict((k.lower(), v) if len(k) > min_upper else 
                             (k,v) for k,v in token2token.items())

    # Remove whitespaces
    token_bs2token = dict((re.sub('\s+', ' ', k).strip(), v) for k,v 
                          in token_lower2token.items())

    # Remove punctuation
    token_punc2token = dict((k.translate(str.maketrans('', '', string.punctuation)), v) for k,v in token_bs2token.items())
    
    # Remove accents
    token_processed2token = dict((remove_accents(k), v) for k,v in token_punc2token.items())
    
    return token_processed2token

def modify_copied_files(new_annots, out_path, with_notes=False):
    '''
    DESCRIPTION: add suggestions (newly discovered annotations) to ann files.
    
    Parameters
    ----------
    new_annots: python dict 
        It has new annotations and the file they belong to. 
        {filename: [annotation1, annotatio2, ]}
    out_path: str
        Path to files.
    with_notes: bool
        whether we are predicting codes, or not
    '''
    files_new_annot = list(new_annots.keys())
    
    for root, dirs, files in os.walk(out_path):
        for filename in files:
            if filename not in files_new_annot:
                continue
            if filename[-3:] != 'txt':
                continue
            filename_ann = filename[0:-3]+ 'ann'
            
            # Get highest mark in ann
            if os.path.exists(os.path.join(root, filename_ann)) == 0:
                mark = 0
                mode = "w"
            else:
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
                mode = "a"
           
            # 2. Write new annotationsgit 
            new_annotations = new_annots[filename]
            with open(os.path.join(root,filename_ann),mode) as file:
                for a in new_annotations:
                    mark = mark + 1
                    file.write('T' + str(mark) + '\t' + '_SUG_' +  a[3] + 
                               ' ' + str(a[1]) + ' ' + str(a[2]) + 
                               '\t' + a[0] + '\n') 
                    if with_notes == False:
                        continue
                    file.write('#' + str(mark) + '\t' + 'AnnotatorNotes' +
                               ' T' + str(mark) + '\t' + a[4] + '\n')                            


def format_ann_info(df_annot, min_upper, with_notes=False):
    '''
    DESCRIPTION: Build useful Python dicts from DataFrame with info from TSV file
    
    Parameters
    ----------
    df_annot: pandas DataFrame 
        With 4 columns: 'filename', 'label', 'code', 'span'
    min_upper: int. 
        It specifies the minimum number of characters of a word to lowercase 
        it (to prevent mistakes with acronyms).
    with_notes: bool
        whether we are predicting codes, or not
        
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
    
    if with_notes==True:
        annot2code = df_annot.groupby('span')['code'].apply(lambda x: x.tolist()).to_dict()
    else:
        annot2code = {}
        
    # Filter codes: remove duplicates and remove empty ONLY if there are annotations
    # with code and others without it
    fclean = lambda x: list(set(filter(None, x) if any(map(lambda x:len(x)>0, x)) else x))
    NEWannot2code = dict((k, fclean(v)) for k,v in annot2code.items())
    
    annot2annot = dict(zip(set_annotations, set_annotations))
    
    # Split values: {'one': 'three two'} must be {'one': ['three', 'two']}   
    annot2annot_split = annot2annot.copy()
    annot2annot_split = dict((k, tokenize(v)) for k,v in annot2annot_split.items())
    
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

    return file2annot, file2annot_processed, annot2label, annot2annot_processed, NEWannot2code


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
    words = tokenize(txt)
    #print(words)
    
    # Remove beginning and end punctuation and whitespaces. 
    words_no_punctuation = list(map(lambda x: x.strip(string.punctuation + ' '), words))
    #print(words_no_punctuation)
    
    # Remove stopwords and single-character words
    large_words = list(filter(lambda x: len(x) > 1, words_no_punctuation))
    #print(large_words)
    words_no_stw = set(filter(lambda x: x.lower() not in STOP_WORDS, large_words))
    #print(words_no_stw)
    # Create dict with words and their positions in text
    words2pos = {}
    for word in words_no_stw:
        occurrences = list(re.finditer(re.escape(word), txt))
        if len(occurrences) == 0:
            print('ERROR: ORIGINAL WORD NOT FOUND IN ORIGINAL TEXT')
            print(word)
        pos = list(map(lambda x: x.span(), occurrences))
        words2pos[word] = pos
        
    #print(words2pos)
    
    # Dictionary relating original words with words processed
    words2words = dict(zip(words_no_stw, words_no_stw))
    words2words_processed = dict((k, remove_accents(k.lower())) if len(k) > min_upper else 
                                (k,remove_accents(k)) for k,v in words2words.items())
    # Map original position to processed word
    words_processed2pos = {}
    for k, v in words2pos.items():
        k_processed = words2words_processed[k]
        if k_processed not in words_processed2pos:
            words_processed2pos[k_processed] = v
        else:
            words_processed2pos[k_processed] = words_processed2pos[k_processed] + v
    
    # Set of transformed words
    words_final = set(words_processed2pos)
    
    return words_final, words_processed2pos
def store_prediction(pos_matrix, predictions, off0, off1, original_label, 
                     original_annot, txt, code):
    '''
    1. Eliminate old predictions contained in the new one (if there were)
    2. Update predictions and pos_matrix lists with new prediction

    Parameters
    ----------
    pos_matrix : list
        List with the positions of the stored predictions. 
        One element per stored prediction (each element is a list of 2 integers)
    predictions : list
        List with the stored predictions. 
        One element per stored prediction (every element is a list of 5:
                                           text of prediction
                                           starting position in document
                                           end position in document
                                           prediction label
                                           prediction code)
    off0 : int
        Starting position of prediction in text.
    off1 : int
        Ending position of prediction in text..
    original_label : str
        Label of prediction in text.
    original_annot : str
        Original annotation.
    txt : str
        Text where the prediction is found.
    code : str
        Prediction code.

    Returns
    -------
    predictions : list
        List with the stored predictions. 
        One element per stored prediction (every element is a list of 5:
                                           text of prediction
                                           starting position in document
                                           end position in document
                                           prediction label
                                           prediction code)
    pos_matrix : list
        List with the positions of the stored predictions. 
        One element per stored prediction (each element is a list of 2 integers)

    '''
                                        
    # 1. Eliminate old annotations if the new one contains them
    pos_matrix, predictions = \
        eliminate_contained_annots(pos_matrix, predictions, off0, off1)
    
    # 2. STORE NEW PREDICTION
    if code != '#$NOCODE$#':
        predictions.append([txt[off0:off1], off0, off1, original_label, code])
    else:
        predictions.append([txt[off0:off1], off0, off1, original_label])
    pos_matrix.append([off0, off1])
                
    return predictions, pos_matrix


def eliminate_contained_annots(pos_matrix, new_annots, off0, off1):
    '''
    DESCRIPTION: function to be used when a new annotation is found. 
              It check whether this new annotation contains in it an already 
              discovered annotation (smaller). In that case, the old (smaller)
              annotation is removed
    '''
    to_eliminate = [pos for item, pos in zip(pos_matrix, range(0, len(new_annots))) 
                    if (off0<=item[0]) & (item[1]<=off1)]
    new_annots = [item for item, pos in zip(new_annots, range(0, len(new_annots)))
                       if pos not in to_eliminate]
    pos_matrix = [item for item in pos_matrix if not (off0<=item[0]) & (item[1]<=off1)]
    
    return pos_matrix, new_annots


def check_surroundings(txt, span, original_annot, n_chars, n_words, 
                       original_label, predictions, pos_matrix,min_upper,code):
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
    token_span2id, id2token_span_pos, token_spans = \
        tokenize_span(large_span_reg, n_words)
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
        
        # Check new annotation (smaller) is not contained in a previously 
        # stored new annotation (larger)
        if not any([(item[0]<=off0) & (off1<= item[1]) for item in pos_matrix]):
            # STORE PREDICTION and eliminate old predictions contained in the new one.
            predictions, pos_matrix = \
                store_prediction(pos_matrix, predictions, off0, off1, 
                                 original_label, original_annot, txt, code)
    except: 
        pass
    
    return predictions, pos_matrix

def remove_redundant_suggestions(datapath):
    '''
    DESCRIPTION: 
    Parameters
    ----------
    datapath : str
        path to folder where Brat files are.

    Returns
    -------
    c : int
        Number of removed suggestions.
    '''
    c = 0
    for root, dirs, files in os.walk(datapath):
        for filename in files:
            if filename[-3:]!= 'ann':
                continue
            try:
                # get only ann files
                f = open(os.path.join(root,filename)).readlines()
    
                offsets = []
                to_delete = []
                
                # 1. Get position of confirmed annotations
                for line in f:
                    if (line[0] == 'T') & (line.split('\t')[1][0:5] != '_SUG_'):
                        splitted = line.split('\t')
                        label_offset = splitted[1].split(' ')
                        if ';' not in label_offset[1:][1]: # Do not store discontinuous annotations
                            offsets.append([int(label_offset[1:][0]),
                                            int(label_offset[1:][1])])
                            
                # 2.1 Get position of suggestions.
                # 2.2 Check suggestions are not contained in any confirmed annotation
                for line in f:
                    if (line[0] == 'T') & (line.split('\t')[1][0:5] == '_SUG_'):
                        splitted = line.split('\t')
                        label_offset = splitted[1].split(' ')
                        new_offset = [int(label_offset[1:][0]), int(label_offset[1:][1])]
    
                        if any(map(lambda x: (x[0] <= new_offset[0]) & 
                                   (x[1] >= new_offset[1]), offsets)):
                            to_delete.append(splitted[0])
                            c = c +1
                                
                # 3. Re-write ann without suggestions that were contained in a
                # confirmed annotation
                with open(os.path.join(root,filename), 'w') as fout:
                    for line in f:
                        if ((line.split('\t')[0] not in to_delete) & 
                            (line.split('\t')[1].split(' ')[1] not in to_delete)):
                            fout.write(line)
            except:
                print('This file retrieved an error {}, please check the ANN file to see what is going on', format(filename))
    return c