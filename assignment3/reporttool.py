#functionally a copy of loader.py that runs queries from a file and outputs the results into another file
import argparse

from support import *
from nltk.stem import PorterStemmer
import math
from time import perf_counter
from statistics import median
import csv

from loader import loadIndex,readMetadataStage1,readMetadataStage2,getFileReader,calcScoreBM25,calcScoreVector,searchFile,BoostPositionPost


def parseQueryFile(path):
    queries = {}
    with open(path,"r") as f:
        text = f.readlines()
    current = ""
    for line in text:
        if not line or line.isspace(): #empty line
            continue
        if line.startswith("Q:"): #new query
            query = line.split("Q:",1)[1].replace("\n", "")
            queries[query] = {}
            current = query
        else: #query results
            doc = line.split("\t")
            queries[current][doc[0]] = int(doc[1])
    return queries


def searchInfo(index,stemmer,metadata,scorefunc,queries,sizes,queryRepeats):
    
    info = {x:{"normal":{"precision":0,"recall":0,"fmeasure":0,"AP":0,"NDCG":0,"latency":0,"throughput":[]},
               "boost":{"precision":0,"recall":0,"fmeasure":0,"AP":0,"NDCG":0,"latency":0,"throughput":[]}} for x in sizes}

    queryCount = len(queries.keys())

    for query,standard in queries.items():
        queryTimeNoBoostList = []
        queryTimeBoostList = []
        for _ in range(queryRepeats):
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

            queryTimeNoBoostList.append(queryTimeNoBoost)
            queryTimeBoostList.append(queryTimeBoost)

        # Gonna do boosting for each set for more accurate timing
        for x in sizes:
    
            # Median query latency
            info[x]["normal"]["latency"] += median(queryTimeNoBoostList)
            info[x]["boost"]["latency"] += median(queryTimeBoostList)

            # List of all latencies for later average query throughput calculation
            info[x]["normal"]["throughput"].extend(queryTimeNoBoostList)
            info[x]["boost"]["throughput"].extend(queryTimeBoostList)

            for boost,results in [("normal",top50Base),("boost",top50Boost)]:
                top = set(results[:x])
                
                # Precision, recall and F-measure
                precision = len(top.intersection(standard.keys()))/len(top)
                recall = len(top.intersection(standard.keys()))/len(standard.keys())
                if precision != 0 and recall != 0:
                    fmeasure = 2*precision*recall/(precision+recall)
                else:
                    fmeasure = 0
                info[x][boost]["precision"] += precision
                info[x][boost]["recall"] += recall
                info[x][boost]["fmeasure"] += fmeasure
                
                # Average precision (AP)
                avgprecision = 0
                for limsize in range(1, x):
                    smallertop = set(results[:limsize])
                    avgprecision += len(smallertop.intersection(standard.keys()))/len(smallertop)
                info[x][boost]["AP"] += avgprecision/x
                
                # Normalized discounted cumulative gain (NDCG)
                dcg = 0
                for idx,item in enumerate(results[:x]):
                    idx = idx+2
                    rel = standard.get(item,0)
                    dcg += rel/math.log2(idx)
                idcg = 0
                for idx,item in enumerate(sorted(results[:x], reverse=True, key=lambda x: standard.get(x,0))):
                    idx = idx+2
                    rel = standard.get(item,0)
                    idcg += rel/math.log2(idx)
                if idcg != 0:
                    info[x][boost]["NDCG"] += dcg/idcg

    for size in sizes:
        for boost in ["normal","boost"]:

            # Average query throughput
            info[size][boost]["throughput"] = len(info[size][boost]["throughput"])/sum(info[size][boost]["throughput"])

            # Change from sum to average
            for metric in ["latency", "precision", "recall", "fmeasure", "AP", "NDCG"]:
                info[size][boost][metric] /= queryCount

    return info

if __name__=="__main__":
    parser= argparse.ArgumentParser()
    parser.add_argument("--masterfile",help="path to master file",default="masterindex.ssv")
    parser.add_argument("--metadata",help="path to stage 1 metadata",default="stage1metadata.ssv")
    parser.add_argument("--metadata2",help="path to stage 2 metadata",default="stage2metadata.ssv")
    parser.add_argument("--prefix",help="Index file prefix",default="mergedindex")
    parser.add_argument('--stemmer', dest='stem', action='store_true')
    parser.add_argument('--no-stemmer', dest='stem', action='store_false')
    parser.add_argument('--BM25', dest='bm25', action='store_true')
    parser.add_argument('--vector', dest='bm25', action='store_false')
    parser.add_argument("--queries",help="Query file source",default="queries.relevance.txt")
    parser.add_argument("--results",help="Result storage file ",default="queryResults.csv")
    parser.add_argument('--pos-window-size',type=int,default=10)
    parser.add_argument("--top",help="List of how many results to use",type=int,nargs="+",default=[10,20,50])
    parser.add_argument("--query-repeats",help="How many times each query is repeated",type=int,default=10)
    parser.add_argument("--append",help="If results are to be appended to the file instead of overwriting", dest="append", action="store_true")
    parser.set_defaults(stem=True, bm25=True, append=False)
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

    info = searchInfo(index,stemmer,metadata,scorefunc,queryDict,args.top,args.query_repeats)
    with open(args.results,"a" if args.append else "w") as f:
        writer = csv.writer(f, delimiter="\t")
        if not args.append:
            writer.writerow(["query","ranking","boost/normal","boost window","precision","recall","fmeasure","AP","NDCG","latency (s)","throughput (q/s)"])
        ranking = "bm25" if args.bm25 else "tf-idf"
        for query,results in info.items():
            for boost in results.keys():
                csvResults = [query, ranking, boost, args.pos_window_size]
                csvResults.extend(list(results[boost].values()))
                writer.writerow(csvResults)
    
    # python indexer.py --lenfilter 3 --prefix data/blockdump --no-stemmer --metadata data/stage1metadata.ssv --source ../amazon_reviews_us_Digital_Music_Purchase_v1_00.tsv.gz --stopsize 500
    # python merger.py --prefix data/block --blocklimit 25000 --masterfile data/bm25/masterindex.ssv --outputprefix data/bm25/mergedindex --metadata data/stage1metadata.ssv --new-metadata data/bm25/stage2metadata.ssv
    # python merger.py --prefix data/block --blocklimit 25000 --masterfile data/vector/masterindex.ssv --outputprefix data/vector/mergedindex --metadata data/stage1metadata.ssv --new-metadata data/vector/stage2metadata.ssv --vector
    # python reporttool.py --masterfile data/bm25/masterindex.ssv --metadata data/stage1metadata.ssv --metadata2 data/bm25/stage2metadata.ssv --prefix data/bm25/mergedindex --no-stemmer --results queryResultsBM25.csv
    # python reporttool.py --masterfile data/vector/masterindex.ssv --metadata data/stage1metadata.ssv --metadata2 data/vector/stage2metadata.ssv --prefix data/vector/mergedindex --no-stemmer --results queryResultsVector.csv --vector