import argparse
import csv
from time import time
from support import *
from nltk.stem import PorterStemmer


def loadIndex(masterfile):
    output = {}
    file = open(masterfile,"r")
    reader = csv.reader(file,delimiter=" ")
    for line in reader:
        output[line[0]] = (line[1],line[2],line[3])
    file.close()
    return output

def searchLoop(index,stemmer,indexprefix):
    print("Entering query mode")
    print("Use '!q' to exit \nMultiple keywords can be used with space separation")
    while True:
        query = input("Input query\n").lower().strip()
        if query =="!q":
            exit()
        
        results = set()
        keywords = query.split(" ")
        try:
            for word in keywords:
                if not results:
                    results.update(searchFile(index[stemmer.stem(word)],indexprefix))
                else:
                    results.intersection_update(searchFile(index[stemmer.stem(word)],indexprefix))
        except KeyError:
            results= set()
        print(f"{len(results)} Documents found:")
        print(sorted(results))

def searchFile(indexentry,indexprefix):
    f = open(f"{indexprefix}{indexentry[1]}.ssv") 
    f.seek(int(indexentry[2]))
    line = f.readline()
    f.close()
    nums = [int(x) for x in line.split(" ")]
    adder = 0
    result = []
    for x in nums:
        adder+=x
        result.append(adder)
    return result
    

if __name__=="__main__":
    parser= argparse.ArgumentParser()
    parser.add_argument("--masterfile",help="path to master file",default="masterindex.ssv")
    parser.add_argument("--prefix",help="Index file prefix",default="mergedindex")
    parser.add_argument("--folder",help="data folder",default=".")
    parser.add_argument('--stemmer', dest='stem', action='store_true')
    parser.add_argument('--no-stemmer', dest='stem', action='store_false')
    parser.set_defaults(stem=True)
    parser.add_argument('--timer-only', dest='timing', action='store_true')
    parser.set_defaults(timing=False)
    args = parser.parse_args()

    if args.stem:
        stemmer = PorterStemmer()
    else:
        stemmer = UselessStemmer()
    if args.timing:
        timedelta = time()
    index = loadIndex(args.masterfile)
    if args.timing:
        timedelta= time()-timedelta
        print(timedelta)
        exit()
    searchLoop(index,stemmer,args.prefix)