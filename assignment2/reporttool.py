import argparse
import csv
from time import time
from support import *
from nltk.stem import PorterStemmer
import math
import json

def readMetadata(metadatafile):
    # unlike the readMetadata in merger.py, this one also stores the real_IDs
    f = open(metadatafile,"r")
    data = f.readline().split(" ")
    data = {"avglen":float(data[1]),"totaldocs":int(data[0])}
    doclens = []
    realids = []
    for line in f:
        row = line.split(" ")
        doclens.append(int(row[2]))
        realids.append(row[1])
    f.close()
    data["lengths"] = doclens
    data["realids"] = realids
    return data

def loadIndex(masterfile):
    output = {}
    file = open(masterfile,"r")
    reader = csv.reader(file,delimiter=" ")
    for line in reader:
        # line = (term, df, fileNum, offset, score/weight)
        output[line[0]] = (line[1],line[2],line[3],line[4])
    file.close()
    return output

def searchInfo(index,stemmer,indexprefix,metadata,scorefunc,queries):
    
    info = {}
    for query in queries:
        query = query.lower().strip()
        allDocs = set()
        termDocs = dict()
        keywords = query.split(" ")
        for word in keywords:
            try:
                if word not in termDocs:
                    docs = searchFile(index[stemmer.stem(word)],indexprefix)
                    allDocs.update(docs.keys())
                    termDocs[word] = (1, docs)
                else:
                    termDocs[word] = (termDocs[word][0]+1, termDocs[word][1])
            except KeyError:
                pass
        
        results = scorefunc(termDocs, allDocs, metadata["totaldocs"], index)
        top100 = [(metadata["realids"][doc], score) for doc, score in sorted(results, key=lambda x: x[1], reverse=True)[0:100]]
        info[query] = { "total":len(results),"docs":top100}
    return info


def searchFile(indexentry,indexprefix):
    #searches for term in file
    #also turns gaps into docIDs
    f = open(f"{indexprefix}{indexentry[1]}.ssv") 
    f.seek(int(indexentry[2]))
    line = f.readline()
    f.close()
    docs = [x.split(":") for x in line.split(" ")]
    adder = 0
    result = dict()
    for num, value in docs:
        num, value = int(num), float(value)
        adder += num
        result[adder] = value
    return result

def calcScoreBM25(termDocs, commonDocs, *_):
    result = []
    for doc in commonDocs:
        score = 0
        for tf, docValues in termDocs.values():
            score += (docValues[doc] if doc in docValues else 0) * tf
        result.append((doc, score))
    return result

def calcScoreVector(termDocs, commonDocs, totaldocs, index):
    result = []
    for doc in commonDocs:
        termWeights = []
        docWeights = []
        for term, (tf, docValues) in termDocs.items():
            termWeights.append((1 + math.log10(tf)) * math.log10(totaldocs/int(index[term][0])))
            docWeights.append(docValues[doc] if doc in docValues else 0)
        queryLen = math.sqrt(sum(w ** 2 for w in termWeights))
        result.append((doc,sum((w/queryLen) * docWeights[i] for i, w in enumerate(termWeights))))
    return result
        
if __name__=="__main__":
    parser= argparse.ArgumentParser()
    parser.add_argument("--masterfile",help="path to master file",default="masterindex.ssv")
    parser.add_argument("--metadata",help="path to stage 1 metadata",default="stage1metadata.ssv")
    parser.add_argument("--prefix",help="Index file prefix",default="mergedindex")
    parser.add_argument('--stemmer', dest='stem', action='store_true')
    parser.add_argument('--no-stemmer', dest='stem', action='store_false')
    parser.set_defaults(stem=True)
    parser.set_defaults(timing=False)
    parser.add_argument('--BM25', dest='bm25', action='store_true')
    parser.add_argument('--vector', dest='bm25', action='store_false')
    parser.set_defaults(bm25=True)
    parser.add_argument("--queries",help="Query file source",default="queries.txt")
    parser.add_argument("--results",help="Result storage file ",default="queryResults.json")
    
    args = parser.parse_args()

    if args.stem:
        stemmer = PorterStemmer()
    else:
        stemmer = UselessStemmer()

    if args.timing:
        timedelta = time()
    index = loadIndex(args.masterfile)
    metadata = readMetadata(args.metadata)
    if args.timing:
        timedelta= time()-timedelta
        print(timedelta)
        exit()

    if args.bm25:
        scorefunc = calcScoreBM25
    else:
        scorefunc = calcScoreVector

    f = open(args.queries,"r")
    queries = f.read().split("\n")
    f.close()

    info = searchInfo(index,stemmer,args.prefix,metadata,scorefunc,queries)
    f = open(args.results,"w")
    json.dump(info,f, indent=4)
    f.close()