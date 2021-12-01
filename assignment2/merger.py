import argparse
import bisect
from support import *
from time import time
import math


def readMetadataHeader(metadatafile):
    f = open(metadatafile,"r")
    data = f.readline.split(" ")
    f.close()
    return {"avglen":float(data[1]),"totaldocs":int(data[0])}

def parseTextLine(line):
    line = line.split(" ")
    freqs = []
    for doc in line[1:]:
        parts = doc.split(":")
        freqs+=(int(parts[0],int(parts[1])))
    return {"word":line[0],"freqs":freqs}

def merge(filenames,termlimit,masterindexfilename,supportfileprefix,totaldocs):
    global_index_struct = []
    consecutive_writes = 0
    curr_file = 0
    files = [open(x,"r") for x in filenames]
    currentwords = {x:parseTextLine(x.readline()) for x in files}
    sortedkeys = sorted(set([x['word'] for x in currentwords.values() ]))

    filewriter = open(f"{supportfileprefix}{curr_file}.ssv","w")
    while sortedkeys:

        current = sortedkeys.pop(0)
        currentwords,gapsandweights,new_terms = iterateAllFiles(current,currentwords)#TODO: CALCUTE WEIGHT BASED ON SETTINGS
        for term in new_terms:
            if term not in sortedkeys:
                bisect.insort(sortedkeys,term)
        docsforterm = len(gapsandweights)
        global_index_struct.append((current,docsforterm,curr_file,filewriter.tell(),math.log10(totaldocs/docsforterm))) #update global index

        filewriter.write(" ".join([f"{numb}:{score}" for numb,score in gapsandweights])+"\n") #write current data to disk
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
    masterindexfile.close()

def iterateAllFiles(current,currentwords): #checks all currently open files, 
    #if they match lowest ranked word we add them to position calculations
    #and try move on, if they dont have more to give we delete them too
    positions = set() 
    new_terms = set()

    for x,y in list(currentwords.items()):
        if y['word']==current:
            docids = [item[0] for item in y["freqs"]] #TODO: SOMETHING ABOUT WEIGHT OR SCORE HERE
            id_adder = 0
            for item in docids:
                id_adder+=item
                positions.add(id_adder)
            next_term = x.readline()
            if next_term=="":
                del currentwords[x]
            else:
                currentwords[x]=parseTextLine(next_term)
                new_terms.add(currentwords[x]["word"])
    
    positions = sorted(positions)
    gaps = [positions[0]]
    for i in range(len(positions))[1:]:
        gaps+= [positions[i]-positions[i-1]]
   
    
    return currentwords,gaps,new_terms


if __name__=="__main__":
    parser= argparse.ArgumentParser()
    parser.add_argument("--prefix",help="prefix for data files",default="block")
    parser.add_argument("--blocklimit",help="how many terms per output file",default=5000)
    parser.add_argument("--masterfile",help="Master file name",default="masterindex.ssv")
    parser.add_argument("--outputprefix",help="prefix for non-master output files",default="mergedindex")
    parser.add_argument("--metadata",help="path to stage 1 metadata",default="stage1metada.ssv")
    parser.add_argument('--BM25', dest='bm25', action='store_true')
    parser.add_argument('--vector', dest='bm25', action='store_false')
    parser.set_defaults(bm25=True)
    parser.add_argument('--BM25-k',type=float,default="1.2")
    parser.add_argument('--BM25-b',type=float,default="0.75")
    args = parser.parse_args()


    metadata = readMetadataHeader(args.metadata)

    timedelta = time()
    files = scanDirectory(args.prefix)
    merge(files,args.blocklimit,args.masterfile,args.outputprefix,metadata['totaldocs'])
    timedelta = time() - timedelta
    print(timedelta)