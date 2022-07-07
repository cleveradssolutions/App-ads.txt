import os
import sys
import json
from datetime import date

rootDir = os.path.dirname(os.path.abspath(__file__))
uniqueSet = set()
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
    "Chartboost.txt", 
    "YandexAds.txt",
    "Fyber.txt",
    "Others.txt",
    #Deprecated:
    #Smaato.txt,
    #StartIo.txt,
]

def printHelpBlock():
    print("Available Operations:")
    print(" no arguments - final App-ads.txt file generation")
    print(" --update SourceName NetworkName [--force]")
    print("      SourceName - file name with new App-ads inventories")
    print("      NetworkName - file name with current network inventories from `Networks` directory.")
    print("      --force - Force update network inventories")

def toUniqueLine(line, source):
    if not line or not line.strip() or line.startswith('#'):
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

if "--help" in sys.argv:
    printHelpBlock()
    exit()

if "--update" in sys.argv:
    tempFileNameIndex = sys.argv.index("--update") + 1
    if tempFileNameIndex >= len(sys.argv) or sys.argv[tempFileNameIndex].startswith('-'):
        print("To use --update option you need set source file name")
        printHelpBlock()
        exit()

    tempFileName = sys.argv[tempFileNameIndex]

    tempFileNameIndex += 1
    if tempFileNameIndex >= len(sys.argv) or sys.argv[tempFileNameIndex].startswith('-'):
        networkFileName = tempFileName
        tempFileName = 'TempUpdate.txt'
    else:
        networkFileName = sys.argv[tempFileNameIndex]
        if '.' not in tempFileName:
            tempFileName += ".txt"
        
    duplicate = 0
    forceGenerate = "--force" in sys.argv
    keepInventories = []
    keepDomain = ""

    with open(rootDir + "/Networks/" + networkFileName + ".txt", 'r') as sourceFile:
        for line in sourceFile:
            if not line or not line.strip() or line.startswith('#'):
                continue
            line = toUniqueLine(line, networkFileName)
            if line in uniqueSet:
                duplicate += 1
                print("Duplicate in source: " + line[:-1])
            elif not keepInventories:
                keepDomain = line.split(',')[0]
                keepInventories.append(line)
            elif line.startswith(keepDomain):
                keepInventories.append(line)
            elif forceGenerate:
                break
            uniqueSet.add(line)

    sourcesCount = len(uniqueSet)
    with open(rootDir + "/" + tempFileName, 'r') as updateFile:
        updateCount = 0
        for line in updateFile:
            if not line or not line.strip() or line.startswith('#') or line.startswith('/'):
                continue
            updateCount += 1
            line = toUniqueLine(line, tempFileName)
            if line not in uniqueSet:
                if not forceGenerate:
                    print("New inventory:\n" + line)
                uniqueSet.add(line)

    if sourcesCount < len(uniqueSet) or duplicate > 0:
        userSelect = 'y' if forceGenerate else raw_input("Write Y when you want update sources or N to exit: ")

        if forceGenerate or userSelect.lower() == 'y':
            with open(rootDir + "/Networks/" + networkFileName + ".txt", 'w') as sourceFile:
                sourceFile.write("#=== " + networkFileName + " " + date.today().strftime("%b %d, %Y") + '\n')
                for line in keepInventories:
                    sourceFile.write(line)
                    uniqueSet.remove(line)

                result = list(uniqueSet)
                result.sort()
                for line in result:
                    sourceFile.write(line)
            print("Updated " + networkFileName + " with " + str(len(uniqueSet) + len(keepInventories)) + " inventories.")
    else:
        print("No new inventory found. ")

    exit()

currentDate = date.today().strftime("%b %d, %Y")
with open(rootDir + "/app-ads.txt", 'w+') as appAdsFile:
    appAdsFile.write("#Last update " + currentDate + '\n')
    for source in sources:
        with open(rootDir + "/Networks/" + source, 'r') as sourceFile:
            for line in sourceFile:
                line = toUniqueLine(line, source)
                if line not in uniqueSet:
                    appAdsFile.write(line)
                    uniqueSet.add(line)

shiledInfo = {
    "schemaVersion": 1,
    "label": "App-ads.txt",
    "message": currentDate,
    "color": "orange"
}

with open(rootDir + "/Shield.json", "w") as shiledFile:
    json.dump(shiledInfo, shiledFile)

print("Combined App-ads.txt with " + str(len(uniqueSet)) + " inventories for " + str(len(sources)) + " networks.")
