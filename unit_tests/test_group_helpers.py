import pytest
import unittest

from discord_bot.group_helpers import howManyGroups


def test_how_many_groups():
    for x in range(1, 105):
        queue = [0] * x
        if x <= 8:
            assert howManyGroups(queue) == 1
        elif x <= 16:
            return howManyGroups(queue) == 2
        elif x <= 24:
            return howManyGroups(queue) == 3
        elif x <= 32:
            return howManyGroups(queue) == 4
        elif x <= 40:
            return howManyGroups(queue) == 5
        elif x <= 48:
            return howManyGroups(queue) == 6
        elif x <= 56:
            return howManyGroups(queue) == 7
        elif x <= 64:
            return howManyGroups(queue) == 8
        elif x <= 72:
            return howManyGroups(queue) == 9
        elif x <= 80:
            return howManyGroups(queue) == 10
        elif x <= 88:
            return howManyGroups(queue) == 11
        elif x <= 96:
            return howManyGroups(queue) == 12
        elif x <= 104:
            return howManyGroups(queue) == 13
