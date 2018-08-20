from lib.common import detokenize
from collections import defaultdict
from copy import deepcopy
import re


re_whitespace = re.compile(r'\s+', flags=re.UNICODE)


class Query:

    agg_ops = ['', 'MAX', 'MIN', 'COUNT', 'SUM', 'AVG']
    cond_ops = ['=', '>', '<', 'OP']
    syms = ['SELECT', 'WHERE', 'AND', 'COL', 'TABLE', 'CAPTION', 'PAGE', 'SECTION', 'OP', 'COND', 'QUESTION', 'AGG', 'AGGOPS', 'CONDOPS']

    def __init__(self, sel_index, agg_index, conditions=tuple(), ordered=False):
        self.sel_index = sel_index
        self.agg_index = agg_index
        self.conditions = list(conditions)
        self.ordered = ordered

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            indices = self.sel_index == other.sel_index and self.agg_index == other.agg_index
            if other.ordered:
                conds = [(col, op, str(cond).lower()) for col, op, cond in self.conditions] == [(col, op, str(cond).lower()) for col, op, cond in other.conditions]
            else:
                conds = set([(col, op, str(cond).lower()) for col, op, cond in self.conditions]) == set([(col, op, str(cond).lower()) for col, op, cond in other.conditions])

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
    def from_dict(cls, d, ordered=False):
        return cls(sel_index=d['sel'], agg_index=d['agg'], conditions=d['conds'], ordered=ordered)

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

    @classmethod
    def from_sequence(cls, sequence, table, lowercase=True):
        sequence = deepcopy(sequence)
        if 'symend' in sequence['words']:
            end = sequence['words'].index('symend')
            for k, v in sequence.items():
                sequence[k] = v[:end]
        terms = [{'gloss': g, 'word': w, 'after': a} for  g, w, a in zip(sequence['gloss'], sequence['words'], sequence['after'])]
        headers = [detokenize(h) for h in table['header']]

        # lowercase everything and truncate sequence
        if lowercase:
            headers = [h.lower() for h in headers]
            for i, t in enumerate(terms):
                for k, v in t.items():
                    t[k] = v.lower()
        headers_no_whitespcae = [re.sub(re_whitespace, '', h) for h in headers]

        # get select
        if 'symselect' != terms.pop(0)['word']:
            raise Exception('Missing symselect operator')

        # get aggregation
        if 'symagg' != terms.pop(0)['word']:
            raise Exception('Missing symagg operator')
        agg_op = terms.pop(0)['word']

        if agg_op == 'symcol':
            agg_op = ''
        else:
            if 'symcol' != terms.pop(0)['word']:
                raise Exception('Missing aggregation column')
        try:
            agg_op = cls.agg_ops.index(agg_op.upper())
        except Exception as e:
            raise Exception('Invalid agg op {}'.format(agg_op))
        
        def find_column(name):
            return headers_no_whitespcae.index(re.sub(re_whitespace, '', name))

        def flatten(tokens):
            ret = {'words': [], 'after': [], 'gloss': []}
            for t in tokens:
                ret['words'].append(t['word'])
                ret['after'].append(t['after'])
                ret['gloss'].append(t['gloss'])
            return ret
        where_index = [i for i, t in enumerate(terms) if t['word'] == 'symwhere']
        where_index = where_index[0] if where_index else len(terms)
        flat = flatten(terms[:where_index])
        try:
            agg_col = find_column(detokenize(flat))
        except Exception as e:
            raise Exception('Cannot find aggregation column {}'.format(flat['words']))
        where_terms = terms[where_index+1:]

        # get conditions
        conditions = []
        while where_terms:
            t = where_terms.pop(0)
            flat = flatten(where_terms)
            if t['word'] != 'symcol':
                raise Exception('Missing conditional column {}'.format(flat['words']))
            try:
                op_index = flat['words'].index('symop')
                col_tokens = flatten(where_terms[:op_index])
            except Exception as e:
                raise Exception('Missing conditional operator {}'.format(flat['words']))
            cond_op = where_terms[op_index+1]['word']
            try:
                cond_op = cls.cond_ops.index(cond_op.upper())
            except Exception as e:
                raise Exception('Invalid cond op {}'.format(cond_op))
            try:
                cond_col = find_column(detokenize(col_tokens))
            except Exception as e:
                raise Exception('Cannot find conditional column {}'.format(col_tokens['words']))
            try:
                val_index = flat['words'].index('symcond')
            except Exception as e:
                raise Exception('Cannot find conditional value {}'.format(flat['words']))

            where_terms = where_terms[val_index+1:]
            flat = flatten(where_terms)
            val_end_index = flat['words'].index('symand') if 'symand' in flat['words'] else len(where_terms)
            cond_val = detokenize(flatten(where_terms[:val_end_index]))
            conditions.append([cond_col, cond_op, cond_val])
            where_terms = where_terms[val_end_index+1:]
        q = cls(agg_col, agg_op, conditions)
        return q

    @classmethod
    def from_partial_sequence(cls, agg_col, agg_op, sequence, table, lowercase=True):
        sequence = deepcopy(sequence)
        if 'symend' in sequence['words']:
            end = sequence['words'].index('symend')
            for k, v in sequence.items():
                sequence[k] = v[:end]
        terms = [{'gloss': g, 'word': w, 'after': a} for  g, w, a in zip(sequence['gloss'], sequence['words'], sequence['after'])]
        headers = [detokenize(h) for h in table['header']]

        # lowercase everything and truncate sequence
        if lowercase:
            headers = [h.lower() for h in headers]
            for i, t in enumerate(terms):
                for k, v in t.items():
                    t[k] = v.lower()
        headers_no_whitespcae = [re.sub(re_whitespace, '', h) for h in headers]

        def find_column(name):
            return headers_no_whitespcae.index(re.sub(re_whitespace, '', name))

        def flatten(tokens):
            ret = {'words': [], 'after': [], 'gloss': []}
            for t in tokens:
                ret['words'].append(t['word'])
                ret['after'].append(t['after'])
                ret['gloss'].append(t['gloss'])
            return ret
        where_index = [i for i, t in enumerate(terms) if t['word'] == 'symwhere']
        where_index = where_index[0] if where_index else len(terms)
        where_terms = terms[where_index+1:]

        # get conditions
        conditions = []
        while where_terms:
            t = where_terms.pop(0)
            flat = flatten(where_terms)
            if t['word'] != 'symcol':
                raise Exception('Missing conditional column {}'.format(flat['words']))
            try:
                op_index = flat['words'].index('symop')
                col_tokens = flatten(where_terms[:op_index])
            except Exception as e:
                raise Exception('Missing conditional operator {}'.format(flat['words']))
            cond_op = where_terms[op_index+1]['word']
            try:
                cond_op = cls.cond_ops.index(cond_op.upper())
            except Exception as e:
                raise Exception('Invalid cond op {}'.format(cond_op))
            try:
                cond_col = find_column(detokenize(col_tokens))
            except Exception as e:
                raise Exception('Cannot find conditional column {}'.format(col_tokens['words']))
            try:
                val_index = flat['words'].index('symcond')
            except Exception as e:
                raise Exception('Cannot find conditional value {}'.format(flat['words']))

            where_terms = where_terms[val_index+1:]
            flat = flatten(where_terms)
            val_end_index = flat['words'].index('symand') if 'symand' in flat['words'] else len(where_terms)
            cond_val = detokenize(flatten(where_terms[:val_end_index]))
            conditions.append([cond_col, cond_op, cond_val])
            where_terms = where_terms[val_end_index+1:]
        q = cls(agg_col, agg_op, conditions)
        return q
