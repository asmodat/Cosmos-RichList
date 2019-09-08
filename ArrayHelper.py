
import json
import time

def GetObjByKey(l,kName,k):
    for kv in l:
        if kv[kName] == k:
            return kv["value"]
    return None


