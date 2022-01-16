import argparse
import csv
from time import perf_counter
from turtle import position
from support import *
from nltk.stem import PorterStemmer
import math


readers = {}

def getFileReader(key):
    if key in readers:
        return readers[key]
    readers[key] = open(f"{getFileReader.prefix}{key}.ssv","r")
    return readers[key]
    

def readMetadataStage1(metadatafile):
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

def readMetadataStage2(metadatafile):
    data = []
    f = open(metadatafile,"r")
    for line in f:
        data.append(float(line))
    f.close()
    return data

def loadIndex(masterfile):
    #now includes IDF
    output = {}
    file = open(masterfile,"r")
    reader = csv.reader(file,delimiter=" ")
    for line in reader:
        # line = (term, df, fileNum, offset, idf)
        output[line[0]] = (line[1],line[2],line[3],line[4])
    file.close()
    return output

def searchLoop(index,stemmer,metadata,scorefunc):
    print("Entering query mode")
    print("Use '!q' to exit \nMultiple keywords can be used with space separation")
    while True:
        query = input("Input query\n").lower().strip()
        if query =="!q":
            exit()
        
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

        results = BoostPosition(keywords,results,positions)

        print(f'{len(results)} documents found, top 100:')
        top100 = [(metadata["realids"][doc], score) for doc, score in sorted(results, key=lambda x: x[1], reverse=True)[0:100]]
        print(*[f'{docID:16s} | {score:7.3f}\n' for docID, score in top100], sep="")

def searchFile(indexentry):
    #searches for term in file
    #also turns gaps into docIDs
    f = getFileReader(indexentry[1])
    f.seek(int(indexentry[2]))
    line = f.readline()
    docs = [x.split(":") for x in line.split(" ")]#ASSIGNMENT 3: THIS CAN NOW HAVE LENGTH 3 IF POSITIONS ARE BEING USED
    adder = 0
    result = dict()
    positions = {}
    for doc in docs:
        num = doc[0]
        value = doc[1]
        num, value = int(num), float(value)
        adder += num
        result[adder] = value
        if len(doc)>2:
            docpos = doc[2].split(",")
            docpos[0] = int(docpos[0])
            for i in range(1,len(docpos)):
                docpos[i] = int(docpos[i]) + docpos[i-1]
            positions[adder] = docpos
    return result,positions

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
            termWeights.append(calcScoreVector.termFreqFunc(tf) * calcScoreVector.docFreqFunc(totaldocs, int(index[term][0])))
            docWeights.append( docValues[doc]/calcScoreVector.normDenums[doc] if doc in docValues else 0)
        queryLen = calcScoreVector.normFunc(termWeights)
        result.append((doc,sum((w/queryLen) * docWeights[i] for i, w in enumerate(termWeights))))
    return result

def BoostPositionPost(query,results,positions):
    windowSize = BoostPositionPost.windowSize
    for document,score in results.keys():
        
        positionVector = []
        for word,positions in positions.items():#for each word we are looking up 
            if document in positions:
                positionVector.extend([(word,x) for x in positions[document]])
        positionVector = sorted(positionVector,key=lambda x:x[1]) #we now have relevant word positions, ordered
        

        word,last_seen = positionVector.pop(0)
        currentState = query.index(word) #no combo yet
        combos = []
        counter = 1
        streak = 0
        for new_word,new_pos in positionVector:
            if new_pos>last_seen+windowSize: #combo over
                combos.append(counter)
                counter = 1
                currentState = query.index(new_word)
                streak = 0
            else:
                pass#TODO: ACTUAL COMBO BOOSTING
        comboScore = sum(combos)/len(combos)
        score*= 1+math.log2(comboScore)/10
    return results

if __name__=="__main__":
    parser= argparse.ArgumentParser()
    parser.add_argument("--masterfile",help="path to master file",default="masterindex.ssv")
    parser.add_argument("--metadata",help="path to stage 1 metadata",default="stage1metadata.ssv")
    parser.add_argument("--metadata2",help="path to stage 2 metadata",default="stage2metadata.ssv")
    parser.add_argument("--prefix",help="Index file prefix",default="mergedindex")
    parser.add_argument('--stemmer', dest='stem', action='store_true')
    parser.add_argument('--no-stemmer', dest='stem', action='store_false')
    parser.set_defaults(stem=True)
    parser.add_argument('--timer-only', dest='timing', action='store_true')
    parser.set_defaults(timing=False)
    parser.add_argument('--BM25', dest='bm25', action='store_true')
    parser.add_argument('--vector', dest='bm25', action='store_false')
    parser.set_defaults(bm25=True)
    parser.add_argument('--term-freq',type=str,default="l")
    parser.add_argument('--doc-freq',type=str,default="t")
    parser.add_argument('--norm',type=str,nargs="+",default=["c"])

    parser.add_argument('--pos', dest='pos',help="enable position boosting", action='store_true')
    parser.add_argument('--no-pos', dest='pos',help="disable position boosting", action='store_false')
    parser.set_defaults(pos=False)
    parser.add_argument('--pos-window-size',type=int,default=10)
    args = parser.parse_args()
    
    if (args.term_freq not in ["n", "l", "b"]):
        raise ValueError("Query term frequency should be in [n, l, b]")
    if (args.norm[0] not in ["n", "c", "u"]):
        raise ValueError("Query normalization should be in [n, c, u]")
    if (args.norm[0] in ["u"]):
        try:
            args.norm[1] = float(args.norm[1])
        except:
            raise ValueError("When query normalization is u, an additional float value is required")
    if (args.doc_freq not in ["n", "t"]):
        raise ValueError("Query document frequency should be in [n, t]")

    if args.stem:
        stemmer = PorterStemmer()
    else:
        stemmer = UselessStemmer()

    if args.timing:
        timedelta = perf_counter()
    index = loadIndex(args.masterfile)
    metadata = readMetadataStage1(args.metadata)
    if args.timing:
        timedelta= perf_counter()-timedelta
        print(timedelta)
        exit()
    if not args.pos:
        BoostPosition = lambda q,x,y: x
    else:
        BoostPositionPost.windowSize = args.pos_window_size
        BoostPosition = BoostPositionPost
    if args.bm25:
        scorefunc = calcScoreBM25
    else:
        scorefunc = calcScoreVector
        
        if (args.term_freq == "n"):
            calcScoreVector.termFreqFunc = lambda tf: tf
        elif (args.term_freq == "l"):
            calcScoreVector.termFreqFunc = lambda tf: 1 + math.log10(tf)
        elif (args.term_freq == "b"):
            calcScoreVector.termFreqFunc = lambda _: 1
        
        if (args.doc_freq == "n"):
            calcScoreVector.docFreqFunc = lambda *_: 1
        elif (args.doc_freq == "t"):
            calcScoreVector.docFreqFunc = lambda N, df: math.log10(N/df)
        
        if (args.norm[0] == "n"):
            calcScoreVector.normFunc = lambda _: 1
        elif (args.norm[0] == "c"):
            calcScoreVector.normFunc = lambda termWeights: math.sqrt(sum(w ** 2 for w in termWeights))
        elif (args.norm[0] == "u"):
            calcScoreVector.normFunc = lambda _: args.norm[1]
        
        calcScoreVector.normDenums = readMetadataStage2(args.metadata2)

    getFileReader.prefix = args.prefix

    searchLoop(index,stemmer,metadata,scorefunc)
