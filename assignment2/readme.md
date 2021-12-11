## Information Review 2021 - Assignment 1
###### by Diogo Bento 93391 and Pedro Laranjinha 93179

## Software
### indexer.py
Generates a series of partial index files based on a provided gzip file.
Output content is partitioned based on the size of the in-memory list structure and its document IDs are sequential, using gaps for storage efficiency.

The tokenizer works by first splitting the text with the regex `[^a-zA-Z]`, which returns a list of purely alphabetical terms, then filtering those terms to remove the ones smaller than the minimum length, the stopwords, and the ones with 4 or more consecutive repeat characters.

This program supports the following parameters:

+ **--lenfilter**: Minimum character length filter, default value is 4 
+ **--stopwords**: Stopword source, A path to a csv file with stopwords. Using 'default' will make the program use the default stopword list
+ **--stopword_delimiter**: Custom delimiter for the stopwords file, default is ","
+ **--stopsize**: Set maximum list size before partitioning in megabytes, default value is 5
+ **--prefix**: Set prefix for output files, default is "blockdump". Output files will always end in .ssv
+ **--stemmer/no-stemmer**: sets whether to use Stemming. By default nltk PorterStemmer is used.
+ **--source**: Input file location
+ **--relevant**: Columns to search, comma-separated
+ **--metadata**: File to output metadata into, default is stage1metadata.ssv

### Features added for 2nd assigment:


### merger.py
Scans for all files matching a preffix and then attempts to merge them.\
It assumes that the content of the files is ordered.\
All files are initially open and the first term of each is used to initialize a priority queue.\
The program then iterates over every file simultaneously for as long as there are terms in the queue.\
The queue is fed new terms as files are iterated.\
Whenever a file runs out of content it is removed from the file pool.

This process leads to the generation of 2 types of files:
1. An index file that has a term, document appearance count, filenumber, and file offset per line
2. Merged index files, containing \n-separated lists of integers which are document IDs and use gaps for storage efficiency   


This program supports the following parameters:
+ **--blocklimit**: Set terms per merged index file, default is 5000
+ **--prefix**: Set prefix for input files, default is "block". Input files are assumed to always end in .ssv
+ **--outputprefix**: Set prefix for output files, default is "mergedindex". Output files have the .ssv extension
+ **--masterfile**: "Master" output file name, default is "masterindex.ssv"

### loader.py
On startup, loads the master index file into a map, with terms as keys.\
Terms can then be searched in a command line interface, opening the "mergedindex" files as needed.\
Use of multiple space-separated terms is supported and will lead to intersection of individual queries.

This program supports the following parameters:
+ **--masterfile**: Master file location, default is "masterindex.ssv"
+ **--prefix**: Prefix to merged index file names, default is "mergedindex"
+ **--stemmer/no-stemmer**: Toggles Stemming, default is using nltk PorterStemmer
+ **--timer-only**: Loads index and exits without going into interactive search mode

### datagen.sh
For each file with the extension `.tsv.gz` in the same folder, it runs `indexer.py` with stop size of 25, `merger.py`, and `loader.py` in timer only mode and measures the time taken, the temporary files created, how many terms the index has, and how much storage the index takes.

### datatable.csv
The output of `datagen.sh` was obtained on a laptop running Kubuntu with an AMD Ryzen 7 5800H and 16GB of RAM.
