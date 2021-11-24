import argparse
import bisect
from support import *
from time import time


def merge(filenames,termlimit,masterindexfilename,supportfileprefix):
    global_index_struct = []
    consecutive_writes = 0
    curr_file = 0

    files = [open(x,"r") for x in filenames]
    currentwords = {x:x.readline() for x in files}
    sortedkeys = sorted(set([x.split(" ")[0] for x in currentwords.values() ]))

    filewriter = open(f"{supportfileprefix}{curr_file}.ssv","w")
    while sortedkeys:

        current = sortedkeys.pop(0)
        currentwords,gaps,new_terms = iterateAllFiles(current,currentwords)
        for term in new_terms:
            if term not in sortedkeys:
                bisect.insort(sortedkeys,term)
        
        global_index_struct.append((current,len(gaps),curr_file,filewriter.tell())) #update global index

        filewriter.write(" ".join([str(numb) for numb in gaps])+"\n") #write current data to disk
        consecutive_writes+=1
        if consecutive_writes>=termlimit:
            consecutive_writes=0
            curr_file+=1
            filewriter.close()
            filewriter = open(f"{supportfileprefix}{curr_file}.ssv","w") #reset file
    masterindexfile = open(masterindexfilename,"w")
    for item in global_index_struct:
        outputstring = f"{item[0]} {item[1]} {item[2]} {item[3]}\n"
        masterindexfile.write(outputstring)
    masterindexfile.close()

def iterateAllFiles(current,currentwords): #checks all currently open files, 
    #if they match lowest ranked word we add them to position calculations
    #and try move on, if they dont have more to give we delete them too
    positions = set() 
    new_terms = set()

    for x,y in list(currentwords.items()):
        splits = y.split(" ")
        if splits[0]==current:
            docids = [int(item) for item in splits[1:]]
            id_adder = 0
            for item in docids:
                id_adder+=item
                positions.add(id_adder)
            next_term = x.readline()
            if next_term=="":
                del currentwords[x]
            else:
                currentwords[x]=next_term
                new_terms.add(next_term.split(" ")[0])
    
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
    args = parser.parse_args()

    timedelta = time()
    files = scanDirectory(args.prefix)
    merge(files,args.blocklimit,args.masterfile,args.outputprefix)
    timedelta = time() - timedelta
    print(timedelta)