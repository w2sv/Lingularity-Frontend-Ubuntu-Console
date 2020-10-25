from typing import Iterator, Optional, List
from itertools import zip_longest

from lingularity.backend.utils.iterables import unzip


def deviation_masks(response: str, ground_truth: str) -> Iterator[Iterator[Optional[bool]]]:
    return unzip(_find_deviations(response, ground_truth))


def _find_deviations(response: str, ground_truth: str) -> Iterator[List[Optional[bool]]]:
    comparators = [response, ground_truth]
    for i, chars_i in enumerate(zip_longest(response, ground_truth)):

        # yield mask elements if chars at parity
        if len(set(chars_i)) == 1:
            yield [False, False]

        else:
            # exit in case of length discrepancy
            if not all(chars_i):
                mask_elements: List[Optional[bool]] = [None, None]

                # iterate over chars_i to determine terminated string
                for j, char_ij in enumerate(chars_i):
                    if not char_ij and chars_i[not j]:
                        mask_elements[not j] = True

                        # yield determined mask values n_remaining_indices times
                        for _ in range(i, len(comparators[not j])):
                            yield mask_elements
                        return

            elif all(len(comparator) >= i + 2 for comparator in comparators):

                # impiaccio <-> impiccio
                if response[i + 1] == ground_truth[i]:
                    yield [True, False]
                    yield from _find_deviations(response[i + 1:], ground_truth[i:])
                    return

                # impicco <-> impiccio
                elif response[i] == ground_truth[i + 1]:
                    yield [False, True]
                    yield from _find_deviations(response[i:], ground_truth[i + 1:])
                    return

            yield [True, True]


if __name__ == '__main__':
    # scossare scorsare

    response_mask, ground_truth_mask = deviation_masks(response='scoprare', ground_truth='scopare')
    print('rm: ', response_mask)
    print('gm: ', ground_truth_mask)
