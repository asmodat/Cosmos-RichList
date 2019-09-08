import json
import statistics

def gini(arr):
    sortedArr = sorted(arr)
    height, area = 0, 0
    for value in sortedArr:
        height += value
        area += height - value / 2.
    fairArea = height * len(arr) / 2.
    return (fairArea - area) / fairArea