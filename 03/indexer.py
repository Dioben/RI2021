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
    postinglist = {}
    for item in reader:
        uniquewordsindoc = set()
        for column_name in relevant_columns:
            text = item[headerdict[column_name]]
            #split text, add individual words
            words = re.split("[^a-zA-Z0-9]",text)#TODO: BETTER TOKENIZER
            uniquewordsindoc.update(words)
            current_items.extend( [(ps.stem(word.lower()),item[headerdict["review_id"]])for word in words if word!=""] ) 
            if psutil.virtual_memory().percent<=MEM_LIMIT_PERCENT: #SORT AND THEN DUMP INTO A BLOCK FILE #TODO: BAD CRITERIA
                outputfile= f"blockdump{current_block}.pickle"
                f = open(outputfile,"wb") #TODO: SHOULD  WRITE TERM->IDS
                current_items = sort_terms(current_items)
                f.write(pickle.dumps(current_items))
                f.close()
                current_items = []
                current_block+=1
        for x in uniquewordsindoc:
            if x in postinglist:
                postinglist[x]+=1
            else:
                postinglist[x]=1

    return postinglist


def sort_terms(array): #DESCRIPTION: SORTS TOKEN SEQUENCE
    return sorted(array,key=lambda x: (x[0],x[1]))

'''
def generate_final_index(ordered): #DESCRIPTION: MAPS ORDERED TERMS TO (TERMS,#DOC)->DOC_SET
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
                index[(current,len(postlingslist))]=postlingslist #save
            #reset
            current = term
            postlingslist= set()
        #update
        postlingslist.add(id)

    return index
'''
if __name__=="__main__":
    f = gzip.open("amazon_reviews_us_Digital_Video_Games_v1_00.tsv.gz","rt")
    relevant_columns= ["product_title","review_headline","review_body"]
    postinglist = process_file(f,"\t",relevant_columns)
    f.close()
    print(postinglist)