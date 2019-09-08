
import json
import time

def FixToAsciiN(s, c, N):
    asciiStr=(s.encode()[:N]).decode("ascii", "ignore")
    return asciiStr + (c * (N - len(asciiStr)))


