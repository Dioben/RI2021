#functionally a copy of loader.py that runs queries from a file and outputs the results into another file
import argparse
from support import *
from nltk.stem import PorterStemmer

from loader import loadIndex,readMetadata,calcScoreBM25,calcScoreVector,searchFile
        

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
        info[query] = top100
    return info


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
    parser.add_argument("--results",help="Result storage file ",default="queryResults.txt")
    
    args = parser.parse_args()

    if args.stem:
        stemmer = PorterStemmer()
    else:
        stemmer = UselessStemmer()

    index = loadIndex(args.masterfile)
    metadata = readMetadata(args.metadata)

    if args.bm25:
        scorefunc = calcScoreBM25
    else:
        scorefunc = calcScoreVector

    f = open(args.queries,"r")
    queries = f.read().split("\n")
    f.close()

    info = searchInfo(index,stemmer,args.prefix,metadata,scorefunc,queries)
    f = open(args.results,"w")
    for query,results in info.items():
        f.write(f"{query}\n")
        for ID,score in results:
            f.write(f"{ID} {score}\n")
        f.write("\n")
    f.close()