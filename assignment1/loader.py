import argparse
import csv

def loadIndex(masterfile):
    output = {}
    file = open(masterfile,"r")
    reader = csv.reader(file,delimiter=" ")
    for line in reader:
        output[line[0]] = (line[1],line[2],line[3])
    file.close()
    return output

def searchLoop(index):#TODO: SUPPORT STEMMERS HERE
    while True:#TODO: infinite loop search
        query = input("Input query,'!q' to exit").lower()
        if query =="!q":
            exit()
        
        results = searchFile(index)
        print(results)

def searchFile(index):
    pass #TODO: actually search file,remember to decompress from gaps

if __name__=="__main__":
    parser= argparse.ArgumentParser()
    parser.add_argument("--masterfile",help="path to master file",default="TODO")
    parser.add_argument("--prefix",help="Index file prefix",default="mergedindex")
    parser.add_argument("--folder",help="data folder",default=".")
    args = parser.parse_args()

index = loadIndex(args.masterfile)