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
    #NEW IN ASSIGNMENT 2
    #returns the current word and a (ID,FREQUENCY) tuple list which now are only split and parsed once
    line = line.split(" ")
    freqs = []
    for doc in line[1:]:
        parts = doc.split(":")
        freqs.append( (int(parts[0]),int(parts[1])) )
    return {"word":line[0],"freqs":freqs}

def merge(filenames,termlimit,masterindexfilename,supportfileprefix,totaldocs,iterateFunc,metadataoutput):
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
        currentwords,gapsandweights,new_terms = iterateFunc(current,currentwords)
        for term in new_terms:
            if term not in sortedkeys:
                bisect.insort(sortedkeys,term)
        docsforterm = len(gapsandweights)
        global_index_struct.append((current,docsforterm,curr_file,filewriter.tell(),math.log10(totaldocs/docsforterm))) #update global index

        doc_id=0
        for i, (numb,score) in enumerate(gapsandweights):
            doc_id += numb
            filewriter.write(f"{numb}:")
            
            doc_index_offset = filewriter.tell()
            if doc_id in global_doc_index:
                global_doc_index[doc_id].append((curr_file,doc_index_offset))
            else:
                global_doc_index[doc_id] = [(curr_file,doc_index_offset)]

            filewriter.write(f"{score}"+("" if i + 1 == len(gapsandweights) else " "))
        filewriter.write("\n")

        consecutive_writes+=1
        if consecutive_writes>=termlimit:
            consecutive_writes=0
            curr_file+=1
            filewriter.close()
            filewriter = open(f"{supportfileprefix}{curr_file}.ssv","w") #reset file
    masterindexfile = open(masterindexfilename,"w")
    for item in global_index_struct:
        outputstring = f"{item[0]} {item[1]} {item[2]} {item[3]} {item[4]}\n"
        masterindexfile.write(outputstring)
    metadatafile = open(metadataoutput,"w")
    for key in sorted(global_doc_index.keys()):
        metadatafile.write(" ".join([f"{x[0]},{x[1]}" for x in global_doc_index[key]]) +"\n")
    filewriter.close()
    metadatafile.close()
    masterindexfile.close()


def iterateAllFilesBM25(current,currentwords): #checks all currently open files, 
    #if they match lowest ranked word we add them to position calculations
    #and try move on, if they dont have more to give we delete them too
    
    #calculates BM25 score
    positions = {} 
    new_terms = set()

    for x,y in list(currentwords.items()):
        if y['word']==current:
            id_adder = 0
            for id,freq in y['freqs']:
                id_adder+=id
                if id_adder not in positions:
                    positions[id_adder] = freq
                else:
                    positions[id_adder]+= freq
            next_term = x.readline()
            if next_term=="":
                del currentwords[x]
            else:
                currentwords[x]=parseTextLine(next_term)
                new_terms.add(currentwords[x]["word"])
    
    positionkeys = sorted(positions.keys())

    k = iterateAllFilesBM25.k #just shortening var names, workaround to ensure same interface as the vector method
    b = iterateAllFilesBM25.b
    totaldocs = iterateAllFilesBM25.totaldocs
    avglen = iterateAllFilesBM25.avglen
    lengths = iterateAllFilesBM25.lengths
    df = len(positionkeys) #total docs

    gaps = [(positionkeys[0], calcBM25(positions[positionkeys[0]],df,totaldocs,k,b,avglen,lengths[positionkeys[0]]) )]
    for i in range(len(positionkeys))[1:]:
        gaps+= [ (positionkeys[i]-positionkeys[i-1], calcBM25(positions[positionkeys[i]],df,totaldocs,k,b,avglen,lengths[positionkeys[i]]) )]
   
    
    return currentwords,gaps,new_terms


def calcBM25(tf,df,N,k,b,avgdl,dl):
    return math.log10(N/df) * (k+1)*tf / (k*((1-b)+b*dl/avgdl)+tf)


def iterateAllFilesVector(current,currentwords): #checks all currently open files, 
    #if they match lowest ranked word we add them to position calculations
    #and try move on, if they dont have more to give we delete them too

    #calculates vector score
    positions = {} 
    new_terms = set()

    for x,y in list(currentwords.items()):
        if y['word']==current:
            id_adder = 0
            for id,freq in y['freqs']:
                id_adder+=id
                if id_adder not in positions:
                    positions[id_adder] = freq
                else:
                    positions[id_adder]+= freq
            next_term = x.readline()
            if next_term=="":
                del currentwords[x]
            else:
                currentwords[x]=parseTextLine(next_term)
                new_terms.add(currentwords[x]["word"])
    
    positionkeys = sorted(positions.keys())
    gaps = [(positionkeys[0], (1+math.log10(positions[positionkeys[0]])))]
    for i in range(len(positionkeys))[1:]:
        gaps+= [ (positionkeys[i]-positionkeys[i-1], (1+math.log10(positions[positionkeys[i]])) )]
   
    
    return currentwords,gaps,new_terms

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
    args = parser.parse_args()


    metadata = readMetadata(args.metadata)

    timedelta = perf_counter()
    files = scanDirectory(args.prefix)
    if args.bm25:
        iteratefunc = iterateAllFilesBM25
        iterateAllFilesBM25.k = args.BM25_k
        iterateAllFilesBM25.b = args.BM25_b
        iterateAllFilesBM25.totaldocs = metadata['totaldocs']
        iterateAllFilesBM25.avglen = metadata["avglen"]
        iterateAllFilesBM25.lengths = metadata["lengths"]
    else:
        iteratefunc = iterateAllFilesVector

    merge(files,args.blocklimit,args.masterfile,args.outputprefix,metadata['totaldocs'],iteratefunc,args.new_metadata)
    timedelta = perf_counter() - timedelta
    print(timedelta)