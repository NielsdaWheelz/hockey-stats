"""finite sixteen-subset algebra; callers own physical domains and closure."""

from math import factorial

import numpy as np

from .artifacts import require


FOUR_GROUP_WEIGHTS = np.zeros((4,16),dtype=np.float64)
for _group in range(4):
    for _subset in range(16):
        if _subset&(1<<_group):
            continue
        _k=_subset.bit_count()
        _weight=factorial(_k)*factorial(3-_k)/24
        FOUR_GROUP_WEIGHTS[_group,_subset|1<<_group]+=_weight
        FOUR_GROUP_WEIGHTS[_group,_subset]-=_weight


def four_group_allocation(coalitions):
    values=np.asarray(coalitions,dtype=np.float64)
    require(values.ndim>=1 and values.shape[0]==16 and np.isfinite(values).all(),
            'invalid sixteen-coalition values')
    return np.tensordot(FOUR_GROUP_WEIGHTS,values,axes=(1,0))
