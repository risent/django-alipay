# -*- coding: utf-8 -*-
from urllib import urlencode
from collections import OrderedDict
from hashlib import md5


def params_filter(params):
    newparams =  {k:v for k,v in params.iteritems() if k not in ('sign', 'sign_type') and v != ''}
    od = OrderedDict(sorted(newparams.items(), key=lambda t:t[0]))
    return od

def build_mysign(params, key, sign_type='MD5'):
    l = []
    for k,v in params.items():
        l.append(str(k) + '=' +str(v))
    prestr = '&'.join(l)
    if sign_type == 'MD5':
        return md5(prestr+key).hexdigest()
    return ''
