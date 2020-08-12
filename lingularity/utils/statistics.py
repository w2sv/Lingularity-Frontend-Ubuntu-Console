from typing import List, Iterable

import numpy as np


def get_outliers(distribution: Iterable[int], positive: bool, iqr_coefficient=1.5) -> List[int]:
    distribution = sorted(distribution)
    first_quart, third_quart = map(lambda percentage: np.quantile(distribution, percentage), [0.25, 0.75])
    iqr = third_quart - first_quart

    if positive:
        filter_function = lambda sample: sample > third_quart + iqr * iqr_coefficient
    else:
        filter_function = lambda sample: sample < first_quart - iqr * iqr_coefficient

    return list(filter(filter_function, distribution))
