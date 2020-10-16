import random

import pytest

from lingularity.backend.trainers.base import ForenameConvertor


random.seed(69)


chinese_forename_converter = ForenameConvertor("Chinese", train_english=False)


@pytest.mark.parametrize('sentence_pair,expected_sentence_pair', [
    (
            ["Ask Tom.", "去问汤姆"],
            ['Ask Chih-ming.', '去问志明']
    ),
    (
            ["Mary came in.", "瑪麗進來了。"],
            ['Mei-ling came in.', '美玲進來了。']
    ),
    (
            ["Tom hugged Mary.", "汤姆拥抱了玛丽"],
            ['Chih-ming hugged Li-hua.', '志明拥抱了麗華']
    ),
    (
            ["Tom is ecstatic.", "汤姆兴奋不已。"],
            ['Chih-hao is ecstatic.', '志豪兴奋不已。']
    ),
    (
            ["Mary doesn't wear as much makeup as Alice.", "玛丽没有化爱丽丝那样浓的妆。"],
            ["I-chun doesn't wear as much makeup as Shu-chuan.", '怡君没有化淑娟那样浓的妆。']
    ),
    (
            ["I don't believe Tom's version of the story.", "我不相信汤姆的说法。"],
            ["I don't believe Wen-Hsiung's version of the story.", '我不相信文雄的说法。']
    )
])
def test_forenames_conversion_chinese(sentence_pair, expected_sentence_pair):
    for converted, expected in zip(chinese_forename_converter(sentence_pair), expected_sentence_pair):
        assert converted == expected