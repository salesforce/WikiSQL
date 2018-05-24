import json
from tqdm import tqdm
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.query import Query
from lib.dbengine import DBEngine


if __name__ == '__main__':
    for split in ['train', 'dev', 'test']:
        print('checking {}'.format(split))
        engine = DBEngine('data/{}.db'.format(split))
        n_lines = 0
        with open('data/{}.jsonl'.format(split)) as f:
            for l in f:
                n_lines += 1
        with open('data/{}.jsonl'.format(split)) as f:
            for l in tqdm(f, total=n_lines):
                d = json.loads(l)
                query = Query.from_dict(d['sql'])
    
                # make sure it's executable
                result = engine.execute_query(d['table_id'], query)
                if result:
                    for a, b, c in d['sql']['conds']:
                        if str(c).lower() not in d['question'].lower():
                            raise Exception('Could not find condition {} in question {} for query {}'.format(c, d['question'], query))
                else:
                    raise Exception('Query {} did not execute to a valid result'.format(query))
