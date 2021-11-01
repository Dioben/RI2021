import csv
import re
import gc
import sys
import gzip
import psutil
from nltk.stem import PorterStemmer
import pickle 
import argparse
from support import *

MEM_LIMIT_PERCENT=30
csv.field_size_limit(sys.maxsize)


def process_file(file,delimiter, relevant_columns, min_length, stopwords, stemmer):#DESCRIPTION: LOADS FILE, GETS CSV ARRAY AND A HEADER DICTIONARY
    #NEW FEATURES: CREATES AND DUMPS TOKEN SEQUENCES
    reader = csv.reader(file,delimiter=delimiter)
    #BUILD HEADER
    header = reader.__next__()
    headerdict = {header[i]:i for i in range(len(header))}

    current_block =0
    current_items = []
    for item in reader:
        for column_name in relevant_columns:
            text = item[headerdict[column_name]]
            #split text, add individual words
            words = re.split("[^a-zA-Z0-9]",text)#TODO: BETTER TOKENIZER, consider decompressing list comprehension for better code and supporting combo keywords
            current_items.extend( [(stemmer.stem(word.lower()),item[headerdict["review_id"]])for word in words if len(word)>=min_length and word not in stopwords] ) 
            if psutil.virtual_memory().percent>=MEM_LIMIT_PERCENT: #SORT AND THEN DUMP INTO A BLOCK FILE
                dump_into_file(f"blockdump{current_block}.pickle",current_items)
                del current_items
                gc.collect() #clear memory
                current_items = []
                current_block+=1

    if current_items:
        dump_into_file(f"blockdump{current_block}.pickle",current_items)
    return 

def dump_into_file(outputfile,current_items):
    f = open(outputfile,"wb")
    current_items = sort_terms(current_items)
    alternate_structure_items = restructure_as_map(current_items)
    f.write(pickle.dumps(alternate_structure_items))
    f.close()

def sort_terms(array): #DESCRIPTION: SORTS TOKEN SEQUENCE
    return sorted(array,key=lambda x: (x[0],x[1]))


def restructure_as_map(ordered): #DESCRIPTION: MAPS ORDERED TERMS TO TERMS->DOC_SET
    current = ""
    postlingslist= set()
    index = {}
    """"
    if term is same add to current ID set, add +1
    when term changes save progreess
    """
    for term,id in ordered:
        if current!=term:
            if current!="":
                index[current]=postlingslist #save
            #reset
            current = term
            postlingslist= set()
        #update
        postlingslist.add(id)

    return index



if __name__=="__main__":
    parser= argparse.ArgumentParser()

    #length filter, default 4
    parser.add_argument("--lenfilter",help="Character length filter, 0 means disabled",type=int,default=4)

    #stopword filter
    parser.add_argument("--stopwords",help="stopword source, 'default' uses default list, alternatively you can use a file path to a csv file with stopwords"\
                                        , default="default")
    parser.add_argument("--stopword_delimiter",help="set the delimiter for your stopword file, default is comma",default=",")

    #stemmer
    parser.add_argument('--stemmer', dest='stem', action='store_true')
    parser.add_argument('--no-stemmer', dest='stem', action='store_false')
    parser.set_defaults(feature=True)

    #input file
    parser.add_argument("--source",help="Source file, please provide gzip compatible files", default="amazon_reviews_us_Digital_Video_Games_v1_00.tsv.gz")

    args = parser.parse_args()


    f = gzip.open(args.source,"rt")
    relevant_columns= ["review_headline","review_body"]

    if args.stopwords=="default":
        from nltk.corpus import stopwords
    else:
        stopword_file = open(args.stopwords,"r")    
        stopwords = set(stopword_file.read().split(args.stopword_delimiter))
        stopword_file.close()

    if args.stem:
        stemmer = PorterStemmer()
    else:
        stemmer=UselessStemmer()


    postinglist = process_file(f,"\t",relevant_columns, args.lenfilter,stopwords,stemmer)
    f.close()