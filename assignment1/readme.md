## Information Review 2021 - Assignment 1
###### by Diogo Bento 93391 and Pedro Laranjinha 93179

## Software
### indexer.py
Generates a series of partial index files based on a provided gzip file.
Output content is partitioned based on the size of the in-memory list structure and its document IDs are sequential, using gaps for storage efficiency.

This program supports the following parameters:

+ --lenfilter: Minimum character length filter, default value is 4 
+ --stopwords: Stopword source, A path to a csv file with stopwords. Using 'default' will make the program use the default stopword list
+ --stopword_delimiter: Custom delimiter for the stopwords file, default is ","
+ --stopsize: Set maximum list size before partitioning in megabytes, default value is 5
+ --prefix: Set prefix for output files, default is "blockdump". Output files will always end in .ssv
+ --stemmer/no-stemmer: sets whether to use Stemming. By default nltk PorterStemmer is used.
+ --source: Input file location

### merger.py
Scans for all files matching a preffix and then attempts to merge them.\
Files are supposedly ordered.\
All files are initially open and the first term of each is used to initialize a priority queue.\
The program then iterates over every file simultaneously for as long as there are terms in the queue.\
The queue is fed new terms as files are iterated.\
Whenever a file runs out of content it is removed from the file pool.

This process leads to the generation of 2 types of files:
1. An index file that has a term, document appearance count, filenumber, and file offset per line
2. Merged index files, containing \n-separated lists of integers which are document IDs and use gaps for storage efficiency   


This program supports the following parameters:
+ --blocklimit: Set terms per merged index file, default is 5000
+ --prefix: Set prefix for input files, default is "block". Input files are assumed to always end in .ssv
+ --outputprefix: Set prefix for output files, default is "mergedindex". Output files have the .ssv extension
+ --masterfile: "Master" output file name, default is "masterindex.ssv"
# TODO: REMOVE FOLDER PARAM
### loader.py
