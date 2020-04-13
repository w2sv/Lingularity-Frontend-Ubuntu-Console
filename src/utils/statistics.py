from typing import List, Iterable

import numpy as np


def get_outliers(distribution: Iterable[int], positive: bool, iqr_coeff=1.5) -> List[int]:
    distribution = sorted(distribution)
    first_quart, third_quard = map(lambda percentage: np.quantile(distribution, percentage), [0.25, 0.75])
    iqr = third_quard - first_quart
    if positive:
        return list(filter(lambda sample: sample > third_quard + iqr * iqr_coeff, distribution))
    else:
        return list(filter(lambda sample: sample < first_quart - iqr * iqr_coeff, distribution))
