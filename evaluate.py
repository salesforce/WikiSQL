#!/usr/bin/env python
import json
from argparse import ArgumentParser
from tqdm import tqdm
from lib.dbengine import DBEngine
from lib.query import Query
from lib.common import count_lines
import copy

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('source_file', help='source file for the prediction')
    parser.add_argument('db_file', help='source database for the prediction')
    parser.add_argument('pred_file', help='predictions by the model')
    parser.add_argument('--ordered', action='store_true', help='whether the exact match should consider the order of conditions')
    args = parser.parse_args()

    engine = DBEngine(args.db_file)
    exact_match = []
    exact_match_ddb = []
    with open(args.source_file) as fs, open(args.pred_file) as fp:
        grades = []
        grades_ddb = []
        for ls, lp in tqdm(zip(fs, fp), total=count_lines(args.source_file)):
            eg = json.loads(ls)
            ep = json.loads(lp)
            ddb = copy.deepcopy(ep) # Copy the prediction
            qg = Query.from_dict(eg['sql'], ordered=args.ordered)          
            gold = engine.execute_query(eg['table_id'], qg, lower=True)
            pred = ep.get('error', None)
            qp = None
            if not ep.get('error', None):
                try:
                     # If SELECT * is used with an agg function, then set to the correctly selected column
                    if ep['ddb_query']['sel'] == '*' and eg['sql']['agg'] == 3:
                        ddb['ddb_query']['sel'] =  eg['sql']['sel']
                    qp_ddb = Query.from_dict(ddb['ddb_query'], ordered=args.ordered)
                    pred_ddb = engine.execute_query(eg['table_id'], qp_ddb, lower=True) 
                except Exception as e:
                    pred_ddb = repr(e)
                try:
                    qp = Query.from_dict(ep['query'], ordered=args.ordered)
                    pred = engine.execute_query(eg['table_id'], qp, lower=True)
                except Exception as e:
                    pred = repr(e)
                    
            # This is the correct output
            correct = pred == gold
            correct_ddb = pred_ddb == gold
            # This is the correct query
            match = qp == qg
            match_ddb = qp_ddb == qg
            grades.append(correct)
            grades_ddb.append(correct_ddb)
            exact_match.append(match)
            exact_match_ddb.append(match_ddb)
        print('Here are the incorrect questions:', [i for i, x in enumerate(grades, start=1) if x == 0])
        print(json.dumps({
            'ex_accuracy': sum(grades) / len(grades),
            'lf_accuracy': sum(exact_match) / len(exact_match),
            'ddb_ex_accuracy': sum(grades_ddb) / len(grades_ddb),
            'ddb_lf_accuracy': sum(exact_match_ddb) / len(exact_match_ddb),
            }, indent=2))
