#functionally a copy of loader.py that runs queries from a file and outputs the results into another file
import argparse

from parso import parse
from support import *
from nltk.stem import PorterStemmer
import math
from time import perf_counter

from loader import loadIndex,readMetadataStage1,readMetadataStage2,getFileReader,calcScoreBM25,calcScoreVector,searchFile,BoostPositionPost


def parseQueryFile(path):
    queries = {}
    with open(path,"r") as f:
        text = f.read()
    current = ""
    for line in text:
        if not line: #empty line
            continue
        if line.startswith("Q:"): #new query
            query = line.split("Q:",1)[1]
            queries[query] = {}
            current = query
        else: #query results
            doc = line.split("\t")
            queries[current][doc[0]] = int(doc[1])


def searchInfo(index,stemmer,metadata,scorefunc,queries):
    
    sizes = [10,20,50]
    info = {x:{"normal":{"latency":0, "precision":0,"recall":0,"fscore":0,"AP":0,"NDCG":0},
               "boost":{"latency":0, "precision":0,"recall":0,"fscore":0,"AP":0,"NDCG":0}} for x in sizes}

    queryCount = len(queries.keys())

    for query,standard in queries.items():

        queryTime = perf_counter()
        query = query.lower().strip()
        allDocs = set()
        termDocs = dict()
        positions = {}
        keywords = query.split(" ")
        for word in keywords:
            try:
                if word not in termDocs:
                    docs,pos = searchFile(index[stemmer.stem(word)])
                    positions[word] = pos
                    allDocs.update(docs.keys())
                    termDocs[word] = (1, docs)
                else:
                    termDocs[word] = (termDocs[word][0]+1, termDocs[word][1])
            except KeyError:
                pass
        
        results = scorefunc(termDocs, allDocs, metadata["totaldocs"], index)
        top50Base = [metadata["realids"][doc] for doc, score in sorted(results, key=lambda x: x[1], reverse=True)[0:50]]
        
        queryTimeNoBoost = perf_counter() - queryTime
        resultsBoost = BoostPosition(keywords,results,positions)
        top50Boost = [ metadata["realids"][doc] for doc, score in sorted(resultsBoost, key=lambda x: x[1], reverse=True)[0:50]]
        queryTimeBoost = perf_counter() -queryTime
        #gonna do boosting for each set for more accurate timing
        for x in sizes:
            info[x]["normal"]["latency"]+=queryTimeNoBoost
            info[x]["boost"]["latency"]+=queryTimeBoost
            for type,results in [("normal",top50Base),("boost",top50Boost)]:
                top = set(results[:x])
                precision = len(top.intersection(standard.keys()))/len(top)
                recall = len(top.intersection(standard.keys()))/len(standard.keys())
                fscore = 2*precision*recall/(precision+recall)
                info[x]["precision"] = precision
                info[x]["recall"] = recall
                info[x]["fscore"] = fscore
                avgprecision = 0
                for limsize in range(x):
                    smallertop = set(results[:limsize])
                    avgprecision+=len(smallertop.intersection(standard.keys()))/len(smallertop)
                info[x]["AP"]+= avgprecision/x
                
                dcg = 0
                for idx,item in results[:x]:
                    idx = idx+1
                    rel = standard.get(item,0)
                    dcg += rel/math.log2(idx)
                idcg = 0
                for idx,item in sorted(results[:x], reverse=True, key=lambda x: standard.get(x,0)):
                    idx = idx+1
                    rel = standard.get(item,0)
                    idcg += rel/math.log2(idx)
                info[x]["NDCG"]+= dcg/idcg
                #TODO: THROUGHPUT

    for size in sizes: #change from sum to average
        for type in ["normal"]["boost"]:
            for metric in ["latency","precision","recall","fscore","AP","NDCG"]:
                info[size][type][metric]/= queryCount
                info[size][type][metric]/= queryCount

    return info

if __name__=="__main__":
    parser= argparse.ArgumentParser()
    parser.add_argument("--masterfile",help="path to master file",default="masterindex.ssv")
    parser.add_argument("--metadata",help="path to stage 1 metadata",default="stage1metadata.ssv")
    parser.add_argument("--metadata2",help="path to stage 2 metadata",default="stage2metadata.ssv")
    parser.add_argument("--prefix",help="Index file prefix",default="mergedindex")
    parser.add_argument('--stemmer', dest='stem', action='store_true')
    parser.add_argument('--no-stemmer', dest='stem', action='store_false')
    parser.set_defaults(stem=True)
    parser.add_argument('--BM25', dest='bm25', action='store_true')
    parser.add_argument('--vector', dest='bm25', action='store_false')
    parser.add_argument("--queries",help="Query file source",default="queries_relevance.txt")
    parser.add_argument("--results",help="Result storage file ",default="queryResults.txt")
    parser.add_argument('--pos-window-size',type=int,default=10)
    parser.set_defaults(bm25=True)
    args = parser.parse_args()

    if args.stem:
        stemmer = PorterStemmer()
    else:
        stemmer = UselessStemmer()

    index = loadIndex(args.masterfile)
    metadata = readMetadataStage1(args.metadata)

    if args.bm25:
        scorefunc = calcScoreBM25
    else:
        scorefunc = calcScoreVector
        calcScoreVector.termFreqFunc = lambda tf: 1 + math.log10(tf)
        calcScoreVector.docFreqFunc = lambda N, df: math.log10(N/df)
        calcScoreVector.normFunc = lambda termWeights: math.sqrt(sum(w ** 2 for w in termWeights))
        
        calcScoreVector.normDenums = readMetadataStage2(args.metadata2)

    BoostPositionPost.windowSize = args.pos_window_size
    BoostPosition = BoostPositionPost
    getFileReader.prefix = args.prefix


    queryDict = parseQueryFile(args.queries)


    info = searchInfo(index,stemmer,metadata,scorefunc,queryDict)
    f = open(args.results,"w")
    for query,results in info.items():
        f.write(f"Q: {query}\n")
        for ID,score in results:
            f.write(f"{ID}\n")
    f.close()