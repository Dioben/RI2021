import os

class UselessStemmer():
    def stem(self,word):
        return word

def scanDirectory(prefix): #return all files starting with prefix 
    files = []
    path = os.path.split(prefix)
    dir = path[0]
    if not dir:
        dir = "."
    name = path[1]
    for f in os.listdir(dir):
        if f.startswith(name):
            files+=[dir+"/"+f]
    return files