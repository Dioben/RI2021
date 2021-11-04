import os

class UselessStemmer():
    def stem(self,word):
        return word

def scanDirectory(dir,prefix): #return all files starting with prefix 
    files = []
    for f in os.listdir(dir):
        if f.startswith(prefix):
            files+=[dir+"/"+f]
    return files