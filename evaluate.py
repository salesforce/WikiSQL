#!/usr/bin/env python
import json
from argparse import ArgumentParser
from tqdm import tqdm
from lib.dbengine import DBEngine
from lib.query import Query
from lib.common import count_lines


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('source_file', help='source file for the prediction')
    parser.add_argument('db_file', help='source database for the prediction')
    parser.add_argument('pred_file', help='predictions by the model')
    args = parser.parse_args()

    engine = DBEngine(args.db_file)
    exact_match = []
    with open(args.source_file) as fs, open(args.pred_file) as fp:
        grades = []
        for ls, lp in tqdm(zip(fs, fp), total=count_lines(args.source_file)):
            eg = json.loads(ls)
            ep = json.loads(lp)
            qg = Query.from_dict(eg['sql'])
            gold = engine.execute_query(eg['table_id'], qg, lower=True)
            pred = ep['error']
            qp = None
            if not ep['error']:
                try:
                    qp = Query.from_dict(ep['query'])
                    pred = engine.execute_query(eg['table_id'], qp, lower=True)
                except Exception as e:
                    pred = repr(e)
            correct = pred == gold
            match = qp == qg
            grades.append(correct)
            exact_match.append(match)
        print(json.dumps({
            'ex_accuracy': sum(grades) / len(grades),
            'lf_accuracy': sum(exact_match) / len(exact_match),
            }, indent=2))
