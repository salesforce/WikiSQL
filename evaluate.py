#!/usr/bin/env python
import json
from argparse import ArgumentParser
from tqdm import tqdm
from lib.dbengine import DBEngine
from lib.query import Query
from lib.common import count_lines
import copy
import pandas as pd

def evaluate_wikisql():
    parser = ArgumentParser()
    parser.add_argument('source_file', help='source file for the prediction')
    parser.add_argument('db_file', help='source database for the prediction')
    parser.add_argument('pred_file', help='predictions by the model')
    parser.add_argument('csv_file_location')
    parser.add_argument('--ordered', action='store_true', help='whether the exact match should consider the order of conditions')
    args = parser.parse_args()
    engine = DBEngine(args.db_file)
    exact_match = []
    exact_match_ddb = []
    incorrect_answer = []
    incorrect_pred = []
    correct_answer = []
    with open(args.source_file) as fs, open(args.pred_file) as fp:
        grades = []
        grades_ddb = []
        count = 0
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
            correct = pred == gold # This compares the query output
            correct_ddb = pred_ddb == gold
            # This is the correct query
            match = qp == qg # qg is the query and qp is the prediction query
            match_ddb = qp_ddb == qg
            grades.append(correct) # Query output
            grades_ddb.append(correct_ddb)
            exact_match.append(match) # SQL query itself
            exact_match_ddb.append(match_ddb)       
            # if count == 24:
            #     print('Question num: ', str(count))
            #     print('ex_accuracy: ', str(correct))
            #     print('Pred: ', str(pred))
            #     print('Gold: ', str(gold))
            #     print('lf_accuracy: ', str(match))
            #     print('Pred: ', str(qp))
            #     print('Gold: ', str(qg))
            if match == 0:
                incorrect_answer.append(f'dev_{count}')
                incorrect_pred.append(qp)
                correct_answer.append(qg)
            if correct != correct_ddb:
                print('Question num: ', str(count))
          
            count += 1
        result_list_dict = {
                'Incorrect answer question #': incorrect_answer,
                'Incorrect answer value prediction': incorrect_pred,
                'Correct answer value': correct_answer
                }            
        result_list_df = pd.DataFrame(result_list_dict)
        result_list_df.to_csv(args.csv_file_location)
        output = json.dumps({
            'incorrect_ex_questions': [i for i, x in enumerate(grades) if x == 0],
            'incorrect_lf_questions': [i for i, x in enumerate(exact_match) if x == 0],
            'ex_accuracy': sum(grades) / len(grades), # Compare query output
            'lf_accuracy': sum(exact_match) / len(exact_match), # Compare SQL query itself
            'ddb_ex_accuracy': sum(grades_ddb) / len(grades_ddb),
            'ddb_lf_accuracy': sum(exact_match_ddb) / len(exact_match_ddb),
            }, indent=2)
        print(output)

        return output
evaluate_wikisql()