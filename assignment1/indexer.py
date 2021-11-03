import csv
import re
import gc
import sys
import gzip
from nltk.stem import PorterStemmer
import json
import argparse
from support import *
from time import time

csv.field_size_limit(sys.maxsize)


def process_file(file,delimiter, relevant_columns, min_length, stopwords, stemmer,break_size):#DESCRIPTION: LOADS FILE, GETS CSV ARRAY AND A HEADER DICTIONARY
    #NEW FEATURES: CREATES AND DUMPS TOKEN SEQUENCES, literally the tokenizer apparently
    reader = csv.reader(file,delimiter=delimiter)
    #BUILD HEADER
    header = reader.__next__()
    headerdict = {header[i]:i for i in range(len(header))}

    current_block =0
    current_items = []
    seq_id =0
    for item in reader:
        for column_name in relevant_columns:
            text = item[headerdict[column_name]]
            #split text, add individual words
            words = re.split("[^a-zA-Z]",text)
            for word in words: #decompressed to support combo keywords and the like in the future
                if len(word)<min_length:
                    continue
                word = word.lower()
                if word in stopwords:
                   continue
                current_items.append(( stemmer.stem(word) ,seq_id ))
            if sys.getsizeof(current_items) > 1024*1024*break_size:
                dump_into_file(f"blockdump{current_block}.json",current_items)
                del current_items
                gc.collect() #clear memory
                current_items = []
                current_block+=1
        seq_id+=1
    if current_items:
        dump_into_file(f"blockdump{current_block}.json",current_items)
    return 

def dump_into_file(outputfile,current_items):
    f = open(outputfile,"w")
    current_items = sort_terms(current_items)
    alternate_structure_items = restructure_as_map(current_items)
    for x,y in alternate_structure_items.items():
        f.write(x+" ")
        f.write(" ".join([str(doc) for doc in y])+"\n")
    #f.write(json.dumps(alternate_structure_items))
    f.close()

def sort_terms(array): #DESCRIPTION: SORTS TOKEN SEQUENCE
    return sorted(array,key=lambda x: (x[0],x[1]))


def restructure_as_map(ordered): #DESCRIPTION: MAPS ORDERED TERMS TO TERMS->DOC_SET
    current = ""
    postingslist= set()
    index = {}
    """"
    if term is same add to current ID set, add +1
    when term changes save progreess
    """
    #TODO: MAKE THIS FOLLOW HOW GAPS ACTUALLY WORK, for loop is probably good enough
    for term,id in ordered:
        if current!=term:
            if current!="":
                postingslist = sorted(postingslist)
                gaps = [postingslist[0]]
                for i in range(len(postingslist))[1:]:
                    gaps+= [postingslist[i]-postingslist[i-1]]
                index[current]=gaps #save
            #reset
            current = term
            postingslist= set()
        #update
        postingslist.add(id)

    return index



if __name__=="__main__":
    parser= argparse.ArgumentParser()

    #length filter, default 4
    parser.add_argument("--lenfilter",help="Character length filter, 0 means disabled",type=int,default=4)

    #stopword filter
    parser.add_argument("--stopwords",help="stopword source, 'default' uses default list, alternatively you can use a file path to a csv file with stopwords"\
                                        , default="default")
    parser.add_argument("--stopword_delimiter",help="set the delimiter for your stopword file, default is comma",default=",")
    parser.add_argument("--stopsize",help="Temporary index size limit in MB",type=int, default=5)

    #stemmer
    parser.add_argument('--stemmer', dest='stem', action='store_true')
    parser.add_argument('--no-stemmer', dest='stem', action='store_false')
    parser.set_defaults(stem=True)

    #input file
    parser.add_argument("--source",help="Source file, please provide gzip compatible files", default="amazon_reviews_us_Digital_Video_Games_v1_00.tsv.gz")

    args = parser.parse_args()


    f = gzip.open(args.source,"rt")
    relevant_columns= ["review_headline","review_body"]

    if args.stopwords=="default":
        from nltk.corpus import stopwords as stopword_source
        stopwords = set(stopword_source.words('english'))
    else:
        stopword_file = open(args.stopwords,"r")    
        stopwords = set(stopword_file.read().split(args.stopword_delimiter))
        stopword_file.close()

    if args.stem:
        stemmer = PorterStemmer()
    else:
        stemmer = UselessStemmer()

    timedelta = time()
    postinglist = process_file(f,"\t",relevant_columns, args.lenfilter,stopwords,stemmer,args.stopsize)
    timedelta = time()-timedelta
    print(timedelta)
    f.close()