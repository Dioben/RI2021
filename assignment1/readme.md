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

### loader.py
