from dataclasses import dataclass
import datetime
from typing import Iterable, Iterator

from backend.src.database.user_database import UserDatabase
from backend.src.utils.date import string_2_date

from frontend.src.utils.iterables import first


@dataclass(frozen=True)
class PlotParameters:
    sequence: list[float]
    dates: list[str]
    item_name: str

    @classmethod
    @UserDatabase.receiver
    def assemble(cls, trainer_shortform: str, item_name_plural: str, user_database: UserDatabase):
        # query language training history of respective trainer
        training_chronic = user_database.training_chronic_collection.training_chronic()
        training_chronic = {
            date: day_dict[trainer_shortform] for date, day_dict in training_chronic.items() if day_dict and day_dict.get(trainer_shortform)  # faulty None's amongst trainer dicts
        }

        # get plotting dates
        STARTING_DATE_DELTA = 14

        dates = list(_plotting_dates(training_dates=iter(training_chronic.keys()), starting_date_delta=STARTING_DATE_DELTA))

        # get training item sequences, conduct zero-padding on dates on which no training took place
        sequence = [training_chronic.get(date, 0) for date in dates]

        return cls(sequence, dates, item_name=item_name_plural)

    # def _training_chronic_axis_title(self, item_scores: Sequence[int]) -> str:
    #     if len(item_scores) == 2 and not item_scores[0]:
    #         return "Let's get that graph inflation goin'"
    #
    #     yesterday_exceedance_difference = item_scores[-1] - item_scores[-2] + 1
    #     item_name = [self._item_name_plural, self._item_name][yesterday_exceedance_difference in {-1, 0}]
    #
    #     if yesterday_exceedance_difference >= 0:
    #         return f"Exceeded yesterdays score by {yesterday_exceedance_difference + 1} {item_name}"
    #     return f"{abs(yesterday_exceedance_difference)} {item_name} left to top yesterdays score"


def _plotting_dates(training_dates: Iterable[str], starting_date_delta: int) -> Iterator[str]:
    """ Returns:
            continuous sequences of plotting dates to be seized as x-axis ticks
            starting from earliest day with (todays date - respective date) <= starting_date_delta,
            going up to todays date

    e.g.:
        today = '2020-10-20'
        training_dates = ('2020-07-19', '2020-08-05', '2020-08-10', '2020-08-12', '2020-08-13', '2020-08-14',
        '2020-08-15', '2020-08-16', '2020-09-18', '2020-09-19', '2020-09-20', '2020-09-21', '2020-09-22',
        '2020-09-24', '2020-09-25', '2020-09-26', '2020-09-27', '2020-09-28', '2020-09-29', '2020-09-30',
        '2020-10-06', '2020-10-12', '2020-10-13', '2020-10-14', '2020-10-15', '2020-10-16', '2020-10-17',
        '2020-10-19', '2020-10-20')

        TrainerFrontend._plotting_dates(_training_dates, starting_date_delta=14)
        ['2020-10-06', '2020-10-07', '2020-10-08', '2020-10-09', '2020-10-10', '2020-10-11', '2020-10-12',
        '2020-10-13', '2020-10-14', '2020-10-15', '2020-10-16', '2020-10-17', '2020-10-18', '2020-10-19',
        '2020-10-20'] """

    starting_date = _get_starting_date(training_dates, starting_date_delta)

    while starting_date <= datetime.date.today():
        yield str(starting_date)
        starting_date += datetime.timedelta(days=1)


def _get_starting_date(training_dates: Iterable[str], day_delta: int) -> datetime.date:
    """ Returns:
            earliest date comprised within training_dates for which (todays date - respective date) <= starting_date_delta
            holds true """

    earliest_possible_date: datetime.date = (datetime.date.today() - datetime.timedelta(days=day_delta))

    return first(
        map(string_2_date, training_dates),
        key=lambda date: date >= earliest_possible_date
    )
