import os
import sys
from datetime import date

def toUniqueLine(line, source):
    if not line or line.startswith('#'):
        return line
    pattern = line.split(',')
    if len(pattern) == 3 or len(pattern) == 4:
        pattern[2] = pattern[2].strip().upper()
        if pattern[2] == 'RESELLER' or pattern[2] == 'DIRECT':
            line = pattern[0].strip().lower() + ', ' + pattern[1].strip() + ', ' + pattern[2]
            if len(pattern) == 4 and pattern[3].strip():
                line += ', ' + pattern[3].strip()
            line += '\n'
        else:
            print("Invalid pattern in " + source + ". Must be RESELLER or DIRECT only:\n" + line)
    else:
        print("Invalid pattern in " + source + ". Must consist of 3 or 4 parts:\n" + line)
    return line


rootDir = os.path.dirname(os.path.abspath(__file__))
sources = [ 
    "AdMob.txt",
    "FBAudienceNetwork.txt",
    "AdColony.txt",
    "Pangle.txt",
    "IronSource.txt",
    "AppLovin.txt",
    "UnityAds.txt",
    "Mintegral.txt",
    "Vungle.txt",
    "SuperAwesome.txt",
    "Kidoz.txt",
    "InMobi.txt",
    "MyTarget.txt",
    "Tapjoy.txt",
    "FyberFairBid.txt",
    "Others.txt"
]
uniqueSet = set()

if len(sys.argv) == 4 and sys.argv[1] == "--update":
    duplicate = 0
    with open(rootDir + "/Networks/" + sys.argv[3] + ".txt", 'r') as sourceFile:
        line = sourceFile.readline()
        while line:
            line = toUniqueLine(line, sys.argv[3])
            if line in uniqueSet:
                duplicate += 1
                print("Duplicate in source: " + line[:-1])
            else:
                uniqueSet.add(line)
            line = sourceFile.readline()

    with open(rootDir + "/" + sys.argv[2] + ".txt", 'r') as updateFile:
        updateCount = 0
        for line in updateFile:
            if not line or line.startswith('#') or line.startswith('/'):
                continue
            updateCount += 1
            line = toUniqueLine(line, sys.argv[2])
            if line not in uniqueSet:
                print("New inventory:\n" + line)
    print("Update done: " + sys.argv[2] + "[" + str(updateCount) + "] / " + sys.argv[3] + "[" + str(len(uniqueSet)) + " + " + str(duplicate) + "]")
    exit()


with open(rootDir + "/app-ads.txt", 'w+') as appAdsFile:
    appAdsFile.write("#Last update " + date.today().strftime("%b %d, %Y") + '\n')
    for source in sources:
        with open(rootDir + "/Networks/" + source, 'r') as sourceFile:
            for line in sourceFile:
                line = toUniqueLine(line, source)
                if line not in uniqueSet:
                    appAdsFile.write(line)
                    uniqueSet.add(line)

print("Combined App-ads.txt with " + str(len(uniqueSet)) + " inventories for " + str(len(sources)) + " networks.")
