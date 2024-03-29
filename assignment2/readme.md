## Information Review 2021 - Assignment 1
###### by Diogo Bento 93391 and Pedro Laranjinha 93179

## Software
### indexer.py
Generates a series of partial index files based on a provided gzip file, as well as a global metadata file.
Output content is partitioned based on the size of the in-memory list structure and its document IDs are sequential, using gaps for storage efficiency.

The tokenizer works by first splitting the text with the regex `[^a-zA-Z]`, which returns a list of purely alphabetical terms, then filtering those terms to remove the ones smaller than the minimum length, the stopwords, and the ones with 4 or more consecutive repeat characters.

This program supports the following parameters:

+ **--lenfilter**: Minimum character length filter, default value is 4 
+ **--stopwords**: Stopword source, a path to a csv file with stopwords.  
        Using 'default' will make the program use the default stopword list
+ **--stopword_delimiter**: Custom delimiter for the stopwords file, default is ","
+ **--stopsize**: Set maximum list size before partitioning in megabytes, default value is 5
+ **--prefix**: Set prefix for output files, default is "blockdump". Output files will always end in .ssv
+ **--stemmer/no-stemmer**: sets whether to use Stemming. By default nltk PorterStemmer is used.
+ **--source**: Input file location
+ **--relevant**: Columns to search, comma-separated
+ **--metadata**: File to output metadata into, default is stage1metadata.ssv

### Features added for 2nd assigment:
- Data blocks now include how many times a term in seen in each document  
- Now outputs a metadata file including: 
    + average document length
    + total document count
    + sequential ID, original ID, document length for each document indexed

### merger.py
Scans for all files matching a preffix and then attempts to merge them.\
It assumes that the content of the files is ordered.\
All files are initially open and the first term of each is used to initialize a priority queue.\
The program then iterates over every file simultaneously for as long as there are terms in the queue.\
The queue is fed new terms as files are iterated.\
Whenever a file runs out of content it is removed from the file pool.

This process leads to the generation of 3 types of files:
1. An index file that has a term, document appearance count, filenumber, and file offset per line
2. Merged index files, containing \n-separated lists of value pairs which are document IDs and term scores, and use gaps for storage efficiency   
3. A metadata file that contains the normalization denominator for every file


This program supports the following parameters:
+ **--blocklimit**: Set terms per merged index file, default is 5000
+ **--prefix**: Set prefix for input files, default is "block". Input files are assumed to always end in .ssv
+ **--outputprefix**: Set prefix for output files, default is "mergedindex". Output files have the .ssv extension
+ **--masterfile**: "Master" output file name, default is "masterindex.ssv"
+ **--metadata**: File to read stage 1 metadata from, default is stage1metadata.ssv
+ **--new-metadata**: File to write stage 2 metadata to, default is stage2metadata.ssv
+ **--BM25/vector**: Toggle between BM25 and vector space ranking, default is BM25
+ **--BM25-k**: The k parameter for BM25 ranking, default is 1.2
+ **--BM25-b**: The b parameter for BM25 ranking, default is 0.75
+ **--term-freq**: The document term frequency letter of the SMART notation for the vector space ranking, possible values are [n, l, b], default is l
+ **--doc-freq**: The document document frequency letter of the SMART notation for the vector space ranking, possible values are [n, t], default is n
+ **--norm**: The document normalization letter of the SMART notation for the vector space ranking, possible values are [n, c, u] (pivoted unique normalization (u) uses 1 extra argument for the value), default is c

### Features added for 2nd assigment:
+ Master index now includes IDF data.  
+ Allows for indexing using BM25 or vector space ranking.
+ Weights are now added to the index files, with no normalization.  
+ Many schemas can be used for the vector space ranking.

Outputs a metadata file where each line contains the normalization denominator of the matching file  
Additionally file line parsing is no longer done several times, which has led to a performance increase eclipsed by the downgrade caused by performing score calculations.

### loader.py
On startup, loads the master index file into a map, with terms as keys, as well as the length and real ID of each document from the metadata file.\
If normalization is enabled the stage 2 metadata file will be read as well.  
Terms can then be searched in a command line interface.
The mergedindex files are now only opened once each and kept in a pool.  
Use of multiple space-separated terms is supported. Each term's document set will be joined and the final score values will be decided based on all keywords.

This program supports the following parameters:
+ **--masterfile**: Master file location, default is "masterindex.ssv"
+ **--prefix**: Prefix to merged index file names, default is "mergedindex"
+ **--stemmer/no-stemmer**: Toggles Stemming, default is using nltk PorterStemmer
+ **--timer-only**: Loads index and exits without going into interactive search mode
+ **--metadata**: File to read stage 1 metadata from, default is stage1metadata.ssv
+ **--metadata2**: File to read stage 2 metadata from, default is stage2metadata.ssv
+ **--BM25/vector**: Toggle between BM25 and vector space ranking, default is BM25
+ **--term-freq**: The query term frequency letter of the SMART notation for the vector space ranking, possible values are [n, l, b], default is l
+ **--doc-freq**: The query document frequency letter of the SMART notation for the vector space ranking, possible values are [n, t], default is n
+ **--norm**: The query normalization letter of the SMART notation for the vector space ranking, possible values are [n, c, u] (pivoted unique normalization (u) uses 1 extra argument for the value), default is c

### Features added for 2nd assigment:
+ Now loads IDF data from metadata.
+ Allows for searching using BM25 or vector space ranking.
+ File pool system
+ Customizable Normalization
+ Many schemas can be used for the vector space ranking.

## Results
The results for each query in the **queries.txt** file, using the BM25 and the vector space ranking file, are in the **queryResultsBM25.txt** and in the **queryResultsVector.txt** files respectively.  
The commands used to obtain these files are:
```
python3 indexer.py --no-stemmer --stopsize 50 --source amazon_reviews_us_Digital_Music_Purchase_v1_00.tsv.gz
python3 merger.py
python3 reporttool.py --no-stemmer --results queryResultsBM25.txt
python3 merger.py --vector
python3 reporttool.py --no-stemmer --vector --results queryResultsVector.txt
```
