import csv
import re
import sys
import gzip
from typing import OrderedDict

csv.field_size_limit(sys.maxsize)

def read_file(file,delimiter):
    reader = csv.reader(file,delimiter=delimiter)

    #BUILD HEADER
    header = reader.__next__()
    headerdict = {header[i]:i for i in range(len(header))}

    return reader,headerdict

def generate_repeat_index(relevant_columns):
    repeat_index = []
    #for word in relevant field
    #add word - doc id
    #what is word? simple for now

    for item in reader:
        for column_name in relevant_columns:
            text = item[headerdict[column_name]]
            #split text, add individual words
            words = re.split("[^a-zA-Z0-9]",text)
            repeat_index.extend( [(word.lower(),item[headerdict["review_id"]])for word in words if word!=""] ) #TODO: TRANSFORM WORD WITH LINGUISTIC MODULE
    return repeat_index



def sort_terms(array):
    return sorted(array,key=lambda x: (x[0],x[1]))

def generate_final_index(ordered):
    current = ""
    postlingslist= set()
    index = OrderedDict()
    """"
    if term is same add to current ID set, add +1
    when term changes save progreess
    """
    for term,id in ordered: #TODO: THIS COUNTS # OF TIMES SEEN, SHOULD BE # OF DOCS
        if current!=term:
            if current!="":
                index[(current,len(postlingslist))]=postlingslist #save
            #reset
            current = term
            postlingslist= set()
        #update
        postlingslist.add(id)

    return index

if __name__=="__main__":
    f = gzip.open("amazon_reviews_us_Digital_Video_Games_v1_00.tsv.gz","rt")
    relevant_columns= ["product_title","review_headline","review_body"]

    reader,headerdict = read_file(f,"\t")

    ordered = sort_terms(generate_repeat_index(relevant_columns))
    results = generate_final_index(ordered)
    i=0
    for item in results:
        print(item)
        matching = results[item]
        if len(matching)<5:
            print("matches ", matching )
        i+=1
        if i==50:
            break