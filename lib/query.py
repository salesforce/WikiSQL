from lib.common import detokenize
from collections import defaultdict
from copy import deepcopy
import re

re_whitespace = re.compile(r'\s+', flags=re.UNICODE)


class Query:

    agg_ops = ['', 'MAX', 'MIN', 'COUNT', 'SUM', 'AVG']
    cond_ops = ['=', '>', '<', 'OP']
    syms = ['SELECT', 'WHERE', 'AND', 'COL', 'TABLE', 'CAPTION', 'PAGE', 'SECTION', 'OP', 'COND', 'QUESTION', 'AGG', 'AGGOPS', 'CONDOPS']

    def __init__(self, sel_index, agg_index, conditions=tuple()):
        self.sel_index = sel_index
        self.agg_index = agg_index
        self.conditions = list(conditions)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            indices = self.sel_index == other.sel_index and self.agg_index == other.agg_index
            conds = [(col, op, cond.lower() if isinstance(cond, str) else cond) for col, op, cond in self.conditions] == [(col, op, cond.lower() if isinstance(cond, str) else cond) for col, op, cond in other.conditions]
            return indices and conds
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        return NotImplemented

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __repr__(self):
        rep = 'SELECT {agg} {sel} FROM table'.format(
            agg=self.agg_ops[self.agg_index],
            sel='col{}'.format(self.sel_index),
        )
        if self.conditions:
            rep +=  ' WHERE ' + ' AND '.join(['{} {} {}'.format('col{}'.format(i), self.cond_ops[o], v) for i, o, v in self.conditions])
        return rep

    def to_dict(self):
        return {'sel': self.sel_index, 'agg': self.agg_index, 'conds': self.conditions}

    def lower(self):
        conds = []
        for col, op, cond in self.conditions:
            conds.append([col, op, cond.lower()])
        return self.__class__(self.sel_index, self.agg_index, conds)

    @classmethod
    def from_dict(cls, d):
        return cls(sel_index=d['sel'], agg_index=d['agg'], conditions=d['conds'])

    @classmethod
    def from_tokenized_dict(cls, d):
        conds = []
        for col, op, val in d['conds']:
            conds.append([col, op, detokenize(val)])
        return cls(d['sel'], d['agg'], conds)

    @classmethod
    def from_generated_dict(cls, d):
        conds = []
        for col, op, val in d['conds']:
            end = len(val['words'])
            conds.append([col, op, detokenize(val)])
        return cls(d['sel'], d['agg'], conds)
