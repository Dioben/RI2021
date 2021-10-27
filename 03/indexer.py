import csv
import re
import sys
import gzip
import psutil
from nltk.stem import PorterStemmer
import pickle 

from typing import OrderedDict

MEM_LIMIT_PERCENT=30
csv.field_size_limit(sys.maxsize)

def process_file(file,delimiter, relevant_columns):#DESCRIPTION: LOADS FILE, GETS CSV ARRAY AND A HEADER DICTIONARY
    #NEW FEATURES: CREATES AND DUMPS TOKEN SEQUENCES
    reader = csv.reader(file,delimiter=delimiter)
    ps = PorterStemmer()

    #BUILD HEADER
    header = reader.__next__()
    headerdict = {header[i]:i for i in range(len(header))}

    current_block =0
    current_items = []
    for item in reader:
        for column_name in relevant_columns:
            text = item[headerdict[column_name]]
            #split text, add individual words
            words = re.split("[^a-zA-Z0-9]",text)#TODO: BETTER TOKENIZER
            current_items.extend( [(ps.stem(word.lower()),item[headerdict["review_id"]])for word in words if word!=""] ) 
            if psutil.virtual_memory().percent>=MEM_LIMIT_PERCENT: #SORT AND THEN DUMP INTO A BLOCK FILE #TODO SWAP FOR TOKEN NUMBER OR MEMORY THAT ARRAY IS USING
                dump_into_file(f"blockdump{current_block}.pickle",current_items)
                current_items = []
                current_block+=1

    if current_items:
        dump_into_file(f"blockdump{current_block}.pickle",current_items)
    return 

def dump_into_file(outputfile,current_items):
    f = open(outputfile,"wb") #TODO: SHOULD  WRITE TERM->IDS
    current_items = sort_terms(current_items)
    alternate_structure_items = restructure_as_map(current_items)
    f.write(pickle.dumps(alternate_structure_items))
    f.close()

def sort_terms(array): #DESCRIPTION: SORTS TOKEN SEQUENCE
    return sorted(array,key=lambda x: (x[0],x[1]))


def restructure_as_map(ordered): #DESCRIPTION: MAPS ORDERED TERMS TO TERMS->DOC_SET
    current = ""
    postlingslist= set()
    index = OrderedDict()
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
    f = gzip.open("amazon_reviews_us_Digital_Video_Games_v1_00.tsv.gz","rt")
    relevant_columns= ["product_title","review_headline","review_body"]
    postinglist = process_file(f,"\t",relevant_columns)
    f.close()