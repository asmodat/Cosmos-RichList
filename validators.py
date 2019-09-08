
import GaiaHelper
import StringHelper
import ArrayHelper
import MathHelper
import subprocess
import json
import statistics
import sys
# apt install python-pip
# python3 -m pip install joblib
# python3 -m pip install multiprocessing
# python3 -m pip install joblib
from joblib import Parallel, delayed

atomPrice=2.0
chainId="cosmoshub-2"

print("----- ----- ----- ----- -----")
print("| VALIDATORS CALCULATIONS   |")
print("----- ----- ----- ----- -----")


inflation = float(GaiaHelper.call("gaiacli query minting inflation -o json --chain-id=" + chainId,None,True))
stakingPool = GaiaHelper.call("gaiacli query staking pool -o json --chain-id=" + chainId,None,True)
notBondedTokens=float(stakingPool["not_bonded_tokens"])/1000000
bondedTokens=float(stakingPool["bonded_tokens"])/1000000
jOperators = GaiaHelper.call("gaiacli query staking validators -o json --chain-id=" + chainId,None,True)

totalTokens=notBondedTokens+bondedTokens
bondedRatio=bondedTokens/totalTokens
rewardRatio = inflation/bondedRatio

print("Inflation: " + str(inflation))
print("Reward Rate: " + str(rewardRatio))

cnt=0
operators=[]
delegatorsList=[]
delegationsList={}

print("Validators Count: " + str(len(jOperators)))
for operator in jOperators:
    if operator["status"] != 2: #status 2 means validator is actively participating in the consensus
        continue

    address=operator["operator_address"]
    commission=float(operator["commission"]["rate"]) 
    tokens=float(operator["tokens"])/1000000
    moniker = StringHelper.FixToAsciiN(operator["description"]["moniker"], ".", 24)

    jDelegators = GaiaHelper.call("gaiacli query staking delegations-to " + address + " -o json --chain-id=" + chainId,None,True)

    if jDelegators is None:
        print(jDelegators)
        print("...............................................")
        continue

    #find self delegation address to ensure its not accounted when calculating revenues
    selfDelegationAddress = GaiaHelper.callRaw("echo $(gaiakeyutil $(echo $(gaiakeyutil "+address+") | cut -d ' ' -f 9)) | cut -d ' ' -f 11",True)
    selfDelegations=0
    delegators=0
    delegations=0
    dArr=[]

    for delegator in jDelegators:
        shares=int(float(delegator["shares"])/1000000)
        delegatorAddress=delegator["delegator_address"]
        delegatorsList.append(delegator)
        shareRatio = round(shares/tokens,2)
		
        if (delegatorAddress is None) or (address is None):
            continue

        dArr.append(shares)
        delegators +=1

    result={ 
        "address": address, 
        "moniker": moniker,
        "commission": commission,
        "delegators": delegators,
        "delegations": tokens
        }
    operators.append(result)
    cnt+=1
    sys.stdout.flush()
    print("Loading... (" + str(cnt) + "/100)")

operators = sorted(operators, key=lambda k: k['delegations'], reverse=True)

print("----- ----- ----- ----- -----")
print("| SORTED by STAKE           |")
print("----- ----- ----- ----- -----")

cnt=0
delegatorsMod=5
delegatorsModCount=0
delegationsModCount=0
commissionsModCount=0

for operator in operators:
    delegatorsModCount += operator["delegators"]
    delegationsModCount += operator["delegations"]
    commissionsModCount  += operator["commission"]
    if (cnt + 1) % delegatorsMod == 0:
        print(StringHelper.FixToAsciiN("TOP" + str(cnt + 1), " ", 6) + " average | Delegators: " + str(int(float(delegatorsModCount)/delegatorsMod)) + " | Commissions: " + str(round(commissionsModCount/delegatorsMod, 2)) + " | Delegations: " + str(int(float(delegationsModCount)/delegatorsMod)) )
        delegatorsModCount = 0
        delegationsModCount = 0
        commissionsModCount = 0
    cnt += 1

print("----- ----- ----- ----- -----")
print("| SORTED by COMMISSIONS     |")
print("----- ----- ----- ----- -----")

operators = sorted(operators, key=lambda k: k['commission'], reverse=False)

cnt=0
delegatorsMod=5
delegatorsModCount=0
delegationsModCount=0
commissionsModCount=0

for operator in operators:
    delegatorsModCount += operator["delegators"]
    delegationsModCount += operator["delegations"]
    commissionsModCount  += operator["commission"]
    if (cnt + 1) % delegatorsMod == 0:
        print(StringHelper.FixToAsciiN("TOP" + str(cnt + 1), " ", 6) + " average | Delegators: " + str(int(float(delegatorsModCount)/delegatorsMod)) + " | Commissions: " + str(round(commissionsModCount/delegatorsMod, 2)) + " | Delegations: " + str(int(float(delegationsModCount)/delegatorsMod)) )
        delegatorsModCount = 0
        delegationsModCount = 0
        commissionsModCount = 0
    cnt += 1

print("----- ----- ----- ----- -----")
print("|    OTHER STATISTICS       |")
print("----- ----- ----- ----- -----")
print("Total number delegations: " + str(len(delegatorsList)))

uniqueDelegators=set()
for delegator in delegatorsList:
    uniqueDelegators.add(delegator["delegator_address"])

print("Total number of unique delegators: " + str(len(uniqueDelegators)))
print("----- ----- ----- ----- -----")
testRanges=[10, 20, 40, 80, 160, 360, 720, 1440, 2880, 5760, 11520, 23040, 46080, 92160]
for r in testRanges:
    delegatorsListSub=[]
    for delegator in delegatorsList:
        if float(delegator["shares"]) >= r*1000000:
            delegatorsListSub.append(delegator)
    uniqueDelegatorsSub=set()
    for delegator in delegatorsListSub:
        uniqueDelegatorsSub.add(delegator["delegator_address"])
    print("ATOM" + str(r) + "+ | Delegations:" + str(len(delegatorsListSub)) + " | Delegators: " + str(len(uniqueDelegatorsSub)))


print("----- ----- ----- ----- -----")
print("|    RETURNS PER MONTH      |")
print("----- ----- ----- ----- -----")

operators = sorted(operators, key=lambda k: k['delegations'], reverse=True)

cnt = 0
earningsSum = 0
arr=[]
for operator in operators:
    earning=int((operator["commission"] * operator["delegations"] * inflation) / 12)
    arr.append(earning)
    earningsSum += earning
    print(StringHelper.FixToAsciiN("TOP" + str(cnt + 1), " ", 6) + " | " + operator["moniker"] + " | Earnings: " + str(int(round(earning,0))) + " ATOM" )
    cnt += 1


print("----- ----- ----- ----- -----")
print("Total: $" + str(earningsSum))
print("Average: $" + str(earningsSum/cnt))
print("Median: $" + str(statistics.median(arr)))

print("----- ----- ----- ----- -----")
print("|    GINI COEFFICIENT       |")
print("----- ----- ----- ----- -----")

giniList=[]
for r in range(1000):
    newArr=[]
    for i in arr:
        if i < (r):
            newArr.append(i + (r))
        else:
            newArr.append(i)
    giniList.append(MathHelper.gini(newArr))

print(",".join(map(str,giniList)))

print("----- ----- ----- ----- -----")
print("|  DELEGATIONS DISTRIBUTION  |")
print("----- ----- ----- ----- -----")

delegationsCnt34=[]
delegationsCnt67=[]
delegationsCnt99=[]


for delegatorAddr in uniqueDelegators:
    sum=0.0
    delegations=delegationsList[delegatorAddr]
    cnt=len(delegations)

    for delegation in delegations:
        sum += float(delegation["shares"]) / 1000000

    if sum < 100:
        continue

    delegations.sort(key=lambda x: x["shares"], reverse=True)

    partialSum=0
    partialCnt=0
    countableDelegationMin=sum*0.001 #0.1% 
    for delegation in delegations:
        shares=float(delegation["shares"]) / 1000000
        partialSum += shares
        partialCnt += 1

        len34 = len(delegationsCnt34)
        len67 = len(delegationsCnt67)
        len99 = len(delegationsCnt99)
        if len34 == len67 and len34 == len99 and partialSum/sum >= 0.34:
            delegationsCnt34.append(partialCnt)
        
        if len34 > len67 and partialSum/sum >= 0.67:
            delegationsCnt67.append(partialCnt)

        if len67 > len99 and partialSum/sum >= 0.99:
            delegationsCnt99.append(partialCnt)
            break
        
print("Median34: " + str(statistics.median(delegationsCnt34)))
print("Mean34: " + str(statistics.mean(delegationsCnt34)))
print("Median67: " + str(statistics.median(delegationsCnt67)))
print("Mean67: " + str(statistics.mean(delegationsCnt67)))
print("Median99: " + str(statistics.median(delegationsCnt99)))
print("Mean99: " + str(statistics.mean(delegationsCnt99)))

