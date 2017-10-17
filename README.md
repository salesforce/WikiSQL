# WikiSQL

[![Build Status](https://travis-ci.org/salesforce/WikiSQL.svg?branch=master)](https://travis-ci.org/salesforce/WikiSQL)

A large crowd-sourced dataset for developing natural language interfaces for relational databases. WikiSQL is the dataset released along with our work [Seq2SQL: Generating Structured Queries from Natural Language using Reinforcement Learning](http://arxiv.org/abs/1709.00103).


## Citation

If you use WikiSQL, please cite the following work:

> Victor Zhong, Caiming Xiong, and Richard Socher. 2017. Seq2SQL: Generating Structured Queries from Natural Language using Reinforcement Learning.


## Leaderboard

If you submit papers on WikiSQL, please consider sending a pull request to merge your results onto the leaderboard. By submitting, you acknowledge that your results are obtained purely by training on the training split and tuned on the dev split (e.g. you only evaluted on the test set once).

| Model                                                          | Dev <br /> logical form <br /> accuracy | Dev <br /> execution <br /> accuracy | Test <br /> logical form <br /> accuracy | Test <br /> execution <br /> accuracy |
| :---:                                                          | :---:                                   | :---:                                | :---:                                    | :---:                                 |
| [Baseline<br />(Zhong 2017)](https://arxiv.org/abs/1709.00103) | 23.3                                    | 37.0                                 | 23.4                                     | 35.9                                  |
| [Seq2SQL<br />(Zhong 2017)](https://arxiv.org/abs/1709.00103)  | 49.5                                    | 60.8                                 | 48.3                                     | 59.4                                  |


## Installation

Both the evaluation script as well as the dataset are stored within the repo.
**Only Python 3 is supported** at the moment - I would very much welcome a pull request that ports the code to work with Python 2.
The installation steps are as follows:

```bash
git clone https://github.com/MetaMind/WikiSQL
cd WikiSQL
pip install -r requirements.txt
tar xvjf data.tar.bz2
``` 

This will unpack the data files into a directory called `data`.

## Content and format

Inside the data folder you will find the files in `jsonl` and `db` format.
The former can be read line by line, where each line is a serialized JSON object.
The latter is a SQLite3 database.

### Question, query and table ID

These files are contained in the `*.jsonl` files. A line looks like the following:

```json
{
   "phase":1,
   "question":"who is the manufacturer for the order year 1998?",
   "sql":{
      "conds":[
         [
            0,
            0,
            "1998"
         ]
      ],
      "sel":1,
      "agg":0
   },
   "table_id":"1-10007452-3"
}
```

The fields represent the following:

- `phase`: the phase in which the dataset was collection. We collected WikiSQL in two phases.
- `question`: the natural language question written by the worker.
- `table_id`: the ID of the table to which this question is addressed.
- `sql`: the SQL query corresponding to the question. This has the following subfields:
  - `sel`: the numerical index of the column that is being selected. You can find the actual column from the table.
  - `agg`: the numerical index of the aggregation operator that is being used. You can find the actual operator from `Query.agg_ops` in `lib/query.py`.
  - `conds`: a list of triplets `(column_index, operator_index, condition)` where:
    - `column_index`: the numerical index of the condition column that is being used. You can find the actual column from the table.
    - `operator_index`: the numerical index of the condition operator that is being used. You can find the actual operator from `Query.cond_ops` in `lib/query.py`.
    - `condition`: the comparison value for the condition, in either `string` or `float` type.

### Tables

These files are contained in the `*.tables.jsonl` files. A line looks like the following:

```json
{
   "id":"1-1000181-1",
   "header":[
      "State/territory",
      "Text/background colour",
      "Format",
      "Current slogan",
      "Current series",
      "Notes"
   ],
   "types":[
      "text",
      "text",
      "text",
      "text",
      "text",
      "text"
   ],
   "rows":[
      [
         "Australian Capital Territory",
         "blue/white",
         "Yaa\u00b7nna",
         "ACT \u00b7 CELEBRATION OF A CENTURY 2013",
         "YIL\u00b700A",
         "Slogan screenprinted on plate"
      ],
      [
         "New South Wales",
         "black/yellow",
         "aa\u00b7nn\u00b7aa",
         "NEW SOUTH WALES",
         "BX\u00b799\u00b7HI",
         "No slogan on current series"
      ],
      [
         "New South Wales",
         "black/white",
         "aaa\u00b7nna",
         "NSW",
         "CPX\u00b712A",
         "Optional white slimline series"
      ],
      [
         "Northern Territory",
         "ochre/white",
         "Ca\u00b7nn\u00b7aa",
         "NT \u00b7 OUTBACK AUSTRALIA",
         "CB\u00b706\u00b7ZZ",
         "New series began in June 2011"
      ],
      [
         "Queensland",
         "maroon/white",
         "nnn\u00b7aaa",
         "QUEENSLAND \u00b7 SUNSHINE STATE",
         "999\u00b7TLG",
         "Slogan embossed on plate"
      ],
      [
         "South Australia",
         "black/white",
         "Snnn\u00b7aaa",
         "SOUTH AUSTRALIA",
         "S000\u00b7AZD",
         "No slogan on current series"
      ],
      [
         "Victoria",
         "blue/white",
         "aaa\u00b7nnn",
         "VICTORIA - THE PLACE TO BE",
         "ZZZ\u00b7562",
         "Current series will be exhausted this year"
      ]
   ]
}
```

The fields represent the following:
- `id`: the table ID.
- `header`: a list of column names in the table.
- `rows`: a list of rows. Each row is a list of row entries.

Tables are also contained in a corresponding `*.db` file.
This is a SQL database with the same information.
Note that due to the flexible format of HTML tables, the column names of tables in the database has been symbolized.
For example, for a table with the columns `['foo', 'bar']`, the columns in the database are actually `col0` and `col1`.

## Scripts

`evaluate.py` contains the evaluation script, whose options are:

```
usage: evaluate.py [-h] source_file db_file pred_file

positional arguments:
  source_file  source file for the prediction
  db_file      source database for the prediction
  pred_file    predictions by the model

optional arguments:
  -h, --help   show this help message and exit
```

The `pred_file`, which is supplied by the user, should contain lines of serialized JSON objects.
Each JSON object should contain a `query` field which corresponds to the query predicted for a line in the input `*.jsonl` file and should be similar to the `sql` field of the input.
In particular, it should contain:

- `sel`: the numerical index of the column that is being selected. You can find the actual column from the table.
- `agg`: the numerical index of the aggregation operator that is being used. You can find the actual operator from `Query.agg_ops` in `lib/query.py`.
- `conds`: a list of triplets `(column_index, operator_index, condition)` where:
  - `column_index`: the numerical index of the condition column that is being used. You can find the actual column from the table.
  - `operator_index`: the numerical index of the condition operator that is being used. You can find the actual operator from `Query.cond_ops` in `lib/query.py`.
  - `condition`: the comparison value for the condition, in either `string` or `float` type.

An example predictions file can be found in `test/example.pred.dev.jsonl`.
The `lib` directory contains dependencies of `evaluate.py`.


## Integration Test

We supply a sample predictions file for the dev set in `test/example.pred.dev.jsonl.bz2`.
You can unzip this file using `bunzip2 test/example.pred.dev.jsonl.bz2 -k` to look at what a real predictions file should look like.
We distribute a docker file which installs the necessary dependencies of this library and runs the evaluation script on this file.
The docker file also serves as an example of how to use the evaluation script.

To run the test, first build the image from the root directory:

```bash
docker build -t wikisqltest -f test/Dockerfile .
```

Next, run the image
```bash
docker run --rm --name wikisqltest wikisqltest
```

If everything works correctly, the output should be:

```json
{
  "ex_accuracy": 0.37036632039365774,
  "lf_accuracy": 0.2334609075997813
}
```


## Annotation

In addition to the raw data dump, we also release an optional annotation script that annotates WikiSQL using [Stanford CoreNLP](https://stanfordnlp.github.io/CoreNLP/).
The `annotate.py` script will annotate the query, question, and SQL table, as well as a sequence to sequence construction of the input and output for convenience of using Seq2Seq models.
To use `annotate.py`, you must set up the CoreNLP python client using [Stanford Stanza](https://github.com/stanfordnlp/stanza).
Note that the sequence output contain symbols to delineate the boundaries of fields.
In `lib/query.py` you will also find accompanying functions to reconstruct a query given a sequence output in the annotated format.



## FAQ

I will update this list with frequently asked questions. 

How do you convert HTML table columns to SQL table columns?

> Web tables are noisy and are not directly transferrable into a database. One problem is that SQL column names need to be symbolic whereas web table columns usually have unicode characters, whitespaces etc. To handle this problem, we convert table columns to symbols (e.g. `Player Name` to `col1`) just before executing the query. For the implementation details, please see `evaluate.py`.



## Changelog

- 1.1: Removed examples from each split that have gloss mismatch between the logical form conditions and the annotated question utterance.
