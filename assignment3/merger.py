import argparse
import bisect
from support import *
from time import perf_counter
import math


def readMetadata(metadatafile):
    #NEW IN ASSIGNMENT 2
    #get average doc length, doc count, each doc's length
    f = open(metadatafile,"r")
    data = f.readline().split(" ")
    data = {"avglen":float(data[1]),"totaldocs":int(data[0])}
    doclens = [int(line.split(" ")[2]) for line in f]
    f.close()
    data["lengths"] = doclens
    return data

def parseTextLine(line):
    line = line.split(" ")
    freqs = []
    for doc in line[1:]:
        parts = doc.split(":")
        if len(parts) > 2:
            freqs.append( (int(parts[0]),int(parts[1]),list([int(x) for x in parts[2].split(",")]) ) ) #doc, count,positions
        else:
            freqs.append( (int(parts[0]),int(parts[1])) )
    return {"word":line[0],"freqs":freqs}

def calcGapsVector(positionkeys,positions):
    df = len(positionkeys)
    gaps = [( positionkeys[0], calcGapsVector.termFreqFunc(positions[positionkeys[0]])*calcGapsVector.docFreqFunc(df) )]
    for i in range(len(positionkeys))[1:]:
        gaps+= [ (positionkeys[i]-positionkeys[i-1], calcGapsVector.termFreqFunc(positions[positionkeys[i]])*calcGapsVector.docFreqFunc(df) )]
    return gaps

def calcGapsBM25(positionkeys,positions):
    k = calcGapsBM25.k #just shortening var names, workaround to ensure same interface as the vector method
    b = calcGapsBM25.b
    totaldocs = calcGapsBM25.totaldocs
    avglen = calcGapsBM25.avglen
    lengths = calcGapsBM25.lengths
    df = len(positionkeys) #total docs

    gaps = [(positionkeys[0], calcBM25(positions[positionkeys[0]],df,totaldocs,k,b,avglen,lengths[positionkeys[0]]) )]
    for i in range(len(positionkeys))[1:]:
        gaps+= [ (positionkeys[i]-positionkeys[i-1], calcBM25(positions[positionkeys[i]],df,totaldocs,k,b,avglen,lengths[positionkeys[i]]) )]
    return gaps

def calcBM25(tf,df,N,k,b,avgdl,dl):
    return math.log10(N/df) * (k+1)*tf / (k*((1-b)+b*dl/avgdl)+tf)


def merge(filenames,termlimit,masterindexfilename,supportfileprefix,totaldocs,metadataoutput):
    global_index_struct = []
    global_doc_index = {}
    consecutive_writes = 0
    curr_file = 0
    files = [open(x,"r") for x in filenames]
    currentwords = {x:parseTextLine(x.readline()) for x in files}
    sortedkeys = sorted(set([x['word'] for x in currentwords.values() ]))

    filewriter = open(f"{supportfileprefix}{curr_file}.ssv","w")
    while sortedkeys:

        current = sortedkeys.pop(0)
        currentwords,gapsandweights,new_terms,word_occurence_indexes = iterateAllFiles(current,currentwords)
        
        for term in new_terms:#insort new terms
            if term not in sortedkeys:
                bisect.insort(sortedkeys,term)
        
        docsforterm = len(gapsandweights)
        global_index_struct.append((current,docsforterm,curr_file,filewriter.tell(),math.log10(totaldocs/docsforterm))) #update global index

        doc_id=0
        gapsize = len(gapsandweights)
        
        
        for i, (numb,score) in enumerate(gapsandweights):
            doc_id += numb
            global_doc_index[doc_id] = merge.normAddFunc(doc_id,global_doc_index,score)
            if word_occurence_indexes:
                filewriter.write(f"{numb}:{score}:{','.join([str(x) for x in word_occurence_indexes[doc_id]])}"+("" if i + 1 == gapsize else " "))
            else:
                filewriter.write(f"{numb}:{score}"+("" if i + 1 == gapsize else " "))

        filewriter.write("\n")

        consecutive_writes+=1
        if consecutive_writes>=termlimit:
            consecutive_writes=0
            curr_file+=1
            filewriter.close()
            filewriter = open(f"{supportfileprefix}{curr_file}.ssv","w") #reset file

    filewriter.close()

    with open(masterindexfilename,"w") as masterindexfile:
        for item in global_index_struct:
            outputstring = f"{item[0]} {item[1]} {item[2]} {item[3]} {item[4]}\n"
            masterindexfile.write(outputstring)
    with open(metadataoutput,"w") as metadatafile:
        for key in range(max(global_doc_index.keys())+1):
            if key not in global_doc_index:
                metadatafile.write("0\n")
            else:
                metadatafile.write(f"{merge.normFinalFunc(global_doc_index[key])}\n")


def iterateAllFiles(current,currentwords): #checks all currently open files, 
    #if they match lowest ranked word we add them to position calculations
    #and try move on, if they dont have more to give we delete them too
    positions = {} 
    new_terms = set()
    word_ocurrence_indexes = {}

    for x,y in list(currentwords.items()):
        if y['word']==current:
            id_adder = 0
            for info in y['freqs']:
                id = info[0]
                freq = info[1]
                id_adder+=id
                if id_adder not in positions:
                    positions[id_adder] = freq
                else:
                    positions[id_adder]+= freq
                if len(info)>2: #we're dealing with positions
                    word_ocurrence_gaps = info[2]
                    for i in range(1,len(word_ocurrence_gaps)):
                        word_ocurrence_gaps[i] = word_ocurrence_gaps[i]+word_ocurrence_gaps[i-1] #undo gaps
                    if id_adder in word_ocurrence_indexes:
                        word_ocurrence_indexes[id_adder].extend(word_ocurrence_gaps)
                    else:
                        word_ocurrence_indexes[id_adder] = word_ocurrence_gaps
            next_term = x.readline()
            if next_term=="":
                del currentwords[x]
            else:
                currentwords[x]=parseTextLine(next_term)
                new_terms.add(currentwords[x]["word"])

    positionkeys = sorted(positions.keys())
    gaps = iterateAllFiles.calcGaps(positionkeys,positions)
    
    for x in word_ocurrence_indexes.values():
        x = sorted(x)
        for i in range(1,len(x))[::-1]:
            x[i] = x[i]-x[i-1] #redo gaps

    return currentwords,gaps,new_terms,word_ocurrence_indexes




if __name__=="__main__":
    parser= argparse.ArgumentParser()
    parser.add_argument("--prefix",help="prefix for data files",default="block")
    parser.add_argument("--blocklimit",help="how many terms per output file",default=5000)
    parser.add_argument("--masterfile",help="Master file name",default="masterindex.ssv")
    parser.add_argument("--outputprefix",help="prefix for non-master output files",default="mergedindex")
    parser.add_argument("--metadata",help="path to stage 1 metadata",default="stage1metadata.ssv")
    parser.add_argument("--new-metadata",help="path to stage 2 metadata",default="stage2metadata.ssv")
    parser.add_argument('--BM25', dest='bm25', action='store_true')
    parser.add_argument('--vector', dest='bm25', action='store_false')
    parser.set_defaults(bm25=True)
    parser.add_argument('--BM25-k',type=float,default="1.2")
    parser.add_argument('--BM25-b',type=float,default="0.75")
    parser.add_argument('--term-freq',type=str,default="l")
    parser.add_argument('--doc-freq',type=str,default="n")
    parser.add_argument('--norm',type=str,nargs="+",default=["c"])

    #positions
    parser.add_argument('--positions', dest='pos', action='store_true')
    parser.add_argument('--no-positions', dest='pos', action='store_false')
    parser.set_defaults(pos=True)
    args = parser.parse_args()

    if (args.term_freq not in ["n", "l", "b"]):
        raise ValueError("Document term frequency should be in [n, l, b]")
    if (args.norm[0] not in ["n", "c", "u"]):
        raise ValueError("Document normalization should be in [n, c, u]")
    if (args.norm[0] in ["u"]):
        try:
            args.norm[1] = float(args.norm[1])
        except:
            raise ValueError("When document normalization is u, an additional float value is required")
    if (args.doc_freq not in ["n", "t"]):
        raise ValueError("Document document frequency should be in [n, t]")

    metadata = readMetadata(args.metadata)

    timedelta = perf_counter()
    files = scanDirectory(args.prefix)
    if args.bm25:
        iterateAllFiles.calcGaps = calcGapsBM25
        calcGapsBM25.k = args.BM25_k
        calcGapsBM25.b = args.BM25_b
        calcGapsBM25.totaldocs = metadata['totaldocs']
        calcGapsBM25.avglen = metadata["avglen"]
        calcGapsBM25.lengths = metadata["lengths"]
        merge.normAddFunc = lambda *_: 0
        merge.normFinalFunc = lambda _: 1
    else:
        iterateAllFiles.calcGaps = calcGapsVector
        if (args.term_freq == "n"):
            calcGapsVector.termFreqFunc = lambda tf: tf
        elif (args.term_freq == "l"):
            calcGapsVector.termFreqFunc = lambda tf: 1 + math.log10(tf)
        elif (args.term_freq == "b"):
            calcGapsVector.termFreqFunc = lambda _: 1
        
        if (args.doc_freq == "n"):
            calcGapsVector.docFreqFunc = lambda _: 1
        elif (args.doc_freq == "t"):
            calcGapsVector.docFreqFunc = lambda df: math.log10(metadata['totaldocs']/df)
            
        if (args.norm[0] == "n"):
            merge.normAddFunc = lambda *_: 0 # doesn't matter
            merge.normFinalFunc = lambda _: 1
        elif (args.norm[0] == "c"):
            merge.normAddFunc = lambda doc_id,global_doc_index,score: \
                global_doc_index[doc_id]+score**2 if doc_id in global_doc_index else score**2
            merge.normFinalFunc = lambda adds: math.sqrt(adds)
        elif (args.norm[0] == "u"):
            merge.normAddFunc = lambda *_: 0 # doesn't matter
            merge.normFinalFunc = lambda _: args.norm[1]
    


    merge(files,args.blocklimit,args.masterfile,args.outputprefix,metadata['totaldocs'],args.new_metadata)
    timedelta = perf_counter() - timedelta
    print(timedelta)