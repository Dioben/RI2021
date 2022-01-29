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
+ **--stopsize**: Set maximum list size before partitioning in megabytes, default value is 100
+ **--prefix**: Set prefix for output files, default is "blockdump". Output files will always end in .ssv
+ **--stemmer/no-stemmer**: sets whether to use Stemming. By default no stemmer is used.
+ **--source**: Input file location
+ **--relevant**: Columns to search, comma-separated
+ **--metadata**: File to output metadata into, default is stage1metadata.ssv
+ **--positions/no-positions**: Sets whether to store positions at which word x occurs in document y, default is True
### Features added for 3rd assigment:
- Optionally stores document positions

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
+ **--blocklimit**: Set terms per merged index file, default is 25000
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

### Features added for 3rd assigment:
+ Merges word occurence positions if applicable

### loader.py
On startup, loads the master index file into a map, with terms as keys, as well as the length and real ID of each document from the metadata file.\
If normalization is enabled the stage 2 metadata file will be read as well.  
Terms can then be searched in a command line interface.
Use of multiple space-separated terms is supported. Each term's document set will be joined and the final score values will be decided based on all keywords.
Our score boosting function is not a toggle, in absence of positions no boosting happens by default

This program supports the following parameters:
+ **--masterfile**: Master file location, default is "masterindex.ssv"
+ **--prefix**: Prefix to merged index file names, default is "mergedindex"
+ **--stemmer/no-stemmer**: Toggles Stemming, default is no stemmer
+ **--timer-only**: Loads index and exits without going into interactive search mode
+ **--metadata**: File to read stage 1 metadata from, default is stage1metadata.ssv
+ **--metadata2**: File to read stage 2 metadata from, default is stage2metadata.ssv
+ **--BM25/vector**: Toggle between BM25 and vector space ranking, default is BM25
+ **--term-freq**: The query term frequency letter of the SMART notation for the vector space ranking, possible values are [n, l, b], default is l
+ **--doc-freq**: The query document frequency letter of the SMART notation for the vector space ranking, possible values are [n, t], default is n
+ **--norm**: The query normalization letter of the SMART notation for the vector space ranking, possible values are [n, c, u] (pivoted unique normalization (u) uses 1 extra argument for the value), default is c
+ **--pos-window-size**: parameter related to score boosting, higher values lead to bigger boosts. default is 10

### Features added for 3rd assigment:
+ Applies a score boosting formula that rewards query terms appearing close to one another, especially when matching the original query's order

### Score Boosting Formula:
We apply a multiplicative bonus to the values often by our previous query methods.  
We get all relevant word positions for a given doc and sort them into a timeline.  

We then iterate the timeline in order to calculate "combos". As long as words appear within a set position index of one another (pos-window-size) the combo score is increased.  
Scores start out incrementing by 1 but this value ramps up with combo length in function of how well the combo matches the query sequence.  
Failing to find a follow-up term within the window will cause the combo value to be scored and a new combo to be started.  

At the end the average combo score is calculated and the original score is multiplied by 1 + log2(avgcombo)/25  

Here are some values to help with comprehension of how this boost scales:

| avgcombo | multiplier |
|:--------:|:----------:|
|     1    |     1.0    |
|     2    |    1.04    |
|     3    |   1.0634   |
|     4    |    1.08    |
|     5    |   1.0928   |
|     6    |   1.1034   |
|     7    |   1.1122   |
|     8    |    1.12    |

## Results
The results for each query in the **queries.relevance.txt** file are in the **queryResults.csv** file.

This CSV file has a column for each evaluation metric and 4 others depicting the number of top docs used (**query**), the ranking used (**ranking**), if the the results were boosted (**boost/normal**), and the boost window size used (**boost window**).

The commands used to obtain this file are:
```
$ python indexer.py --lenfilter 3 --prefix data/blockdump --no-stemmer --metadata data/stage1metadata.ssv --source ../amazon_reviews_us_Digital_Music_Purchase_v1_00.tsv.gz

$ python merger.py --prefix data/block --masterfile data/bm25/masterindex.ssv --outputprefix data/bm25/mergedindex --metadata data/stage1metadata.ssv --new-metadata data/bm25/stage2metadata.ssv

$ python merger.py --prefix data/block --masterfile data/vector/masterindex.ssv --outputprefix data/vector/mergedindex --metadata data/stage1metadata.ssv --new-metadata data/vector/stage2metadata.ssv --vector

$ python reporttool.py --masterfile data/bm25/masterindex.ssv --metadata data/stage1metadata.ssv --metadata2 data/bm25/stage2metadata.ssv --prefix data/bm25/mergedindex --no-stemmer --pos-window-size 1

$ for i in 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 25 30 35 40 45 50 100 150 200; do python reporttool.py --masterfile data/bm25/masterindex.ssv --metadata data/stage1metadata.ssv --metadata2 data/bm25/stage2metadata.ssv --prefix data/bm25/mergedindex --no-stemmer --append --no-normal --pos-window-size ${i}; done

$ python reporttool.py --masterfile data/vector/masterindex.ssv --metadata data/stage1metadata.ssv --metadata2 data/vector/stage2metadata.ssv --prefix data/vector/mergedindex --no-stemmer --vector --pos-window-size 1 --append

$ for i in 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 25 30 35 40 45 50 100 150 200; do  python reporttool.py --masterfile data/vector/masterindex.ssv --metadata data/stage1metadata.ssv --metadata2 data/vector/stage2metadata.ssv --prefix data/vector/mergedindex --no-stemmer --vector --append --no-normal --pos-window-size ${i}; done
```
