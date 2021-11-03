import argparse
import os

from nltk.util import pr

def scanDirectory(dir,prefix): #return all files starting with prefix 
    files = []
    for f in os.listdir(dir):
        if f.startswith(prefix):
            files+=[dir+"/"+f]
    return files

if __name__=="__main__":
    parser= argparse.ArgumentParser()
    parser.add_argument("--prefix",help="prefix for data files inside folder",default="block")
    parser.add_argument("--folder",help="data folder",default=".")
    args = parser.parse_args()

    files = scanDirectory(args.folder,args.prefix)
    print(files)