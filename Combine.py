import os
import sys
import json
from datetime import date

# Use 'help' command to print information
def printHelpBlock():
    print("Supported commands:")
    print("   init    - Create TempUpdate.txt file to update network configuration.")
    print("   list    - List of available network names.")
    print("   update <NetworkName> [--force]")
    print("      NetworkName - file name with current network inventories from `Networks` directory.")
    print("      -f --force  - Force update network inventories")
    print("   release - [Also no arguments] Final App-ads.txt file generation.")
    print("   help    - Print help inforamtion") 

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
    "Chartboost.txt", 
    "YandexAds.txt",
    "Fyber.txt",
    "Others.txt",
    #Deprecated:
    #Smaato.txt,
    #StartIo.txt,
]
bannedDomains = [
    # (Reserved by Network name, Banned domain for other Networks)
    ("AdMob", "google.com")
]

def printNetworks():
    print("Available networks: " + ", ".join(map(lambda net: os.path.splitext(net)[0], sources)))

def isDomainAllowed(line, source):
    for domain in bannedDomains:
        if source != domain[0] and line.startswith(domain[1]):
            return False
    return True

def toUniqueLine(line, source):
    if not line or not line.strip() or line.startswith('/'):
        return ""
    if line.startswith('#'):
        return line
    pattern = line.split(',')
    if len(pattern) == 3 or len(pattern) == 4:
        accountType = pattern[2].strip().upper()
        if accountType == 'RESELLER' or accountType == 'DIRECT':
            domainName = pattern[0].strip().lower()
            publisherId = pattern[1].strip().lower()
            line = domainName + ', ' + publisherId + ', ' + accountType
            if len(pattern) == 4:
                endOfLine = pattern[3].split('#')
                certificationId = endOfLine[0].strip().lower()
                if certificationId:
                    line += ', ' + certificationId
                    certificationIdLen = len(certificationId)
                    if certificationIdLen != 9 and certificationIdLen != 16:
                        print(line)
                        print("   Error: Certification authority ID is invalid. It may only contain numbers and lowercase letters, and must be 9 or 16 characters.")
                        return ""
            line += '\n'
        else:
            print(line)
            print("   Error: Invalid pattern in " + source + ". Must be RESELLER or DIRECT only.")
            return ""
    else:
        print(line)
        print("   Error: Invalid pattern in " + source + ". It may only contain 3 or 4 segments.")
        return ""
    return line

def release():
    uniqueSet = set()
    currentDate = date.today().strftime("%b %d, %Y")
    with open(rootDir + "/app-ads.txt", 'w+') as appAdsFile:
        appAdsFile.write("#Last update " + currentDate + '\n')
        for source in sources:
            with open(rootDir + "/Networks/" + source, 'r') as sourceFile:
                for line in sourceFile:
                    line = toUniqueLine(line, source)
                    if line and line not in uniqueSet:
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

def updateNetwork(networkName, force):
    tempFileName = 'TempUpdate.txt'
    duplicate = 0
    foundNews = False
    keepInventories = []
    keepDomain = ""
    sourceSet = set()
    newsSet = set()

    with open(rootDir + "/Networks/" + networkName + ".txt", 'r') as sourceFile:
        for line in sourceFile:
            line = toUniqueLine(line, networkName)
            if not line or line.startswith('#'):
                continue
            if line in sourceSet:
                duplicate += 1
                print("Duplicate in source: " + line[:-1])
                continue
            if not keepInventories:
                keepDomain = line.split(',')[0]
                keepInventories.append(line)
            elif line.startswith(keepDomain):
                keepInventories.append(line)
            sourceSet.add(line)

    with open(rootDir + "/" + tempFileName, 'r') as updateFile:
        for line in updateFile:
            line = toUniqueLine(line, tempFileName)
            if not line or line.startswith('#'):
                continue
            if line and isDomainAllowed(line, networkName):
                newsSet.add(line)
                if line not in sourceSet:
                    print("New inventory:\n" + line)
                    foundNews = True


    if foundNews or duplicate > 0 or len(newsSet) > len(sourceSet):
        userSelect = 'f' if force else raw_input("Enter Y (to add new inventories), F (to force remove obsolute inventories) or N (to exit): ")

        if userSelect.lower() == 'f':
            force = True
        else:
            newsSet.update(sourceSet)

        if force or userSelect.lower() == 'y':
            with open(rootDir + "/Networks/" + networkName + ".txt", 'w') as sourceFile:
                sourceFile.write("#=== " + networkName + " " + date.today().strftime("%b %d, %Y") + '\n')
                for line in keepInventories:
                    sourceFile.write(line)
                    newsSet.remove(line)

                result = list(newsSet)
                result.sort()
                for line in result:
                    if isDomainAllowed(line, networkName):
                        sourceFile.write(line)
            print("Updated " + networkName + " with " + str(len(result) + len(keepInventories)) + " inventories.")
    else:
        print("No found inventories to update.")

if len(sys.argv) == 1:
    release()
    sys.exit()

index = 1
while index < len(sys.argv):
    command = sys.argv[index]
    if "init" == command:
        open(rootDir + "/TempUpdate.txt", 'w+').close()
    elif "list" == command:
        printNetworks()
    elif "release" == command:
        release()
    elif "update" == command:
        index += 1
        if index < len(sys.argv) and not sys.argv[index].startswith('-'):
            targetNetwork = sys.argv[index]
            if index + 1 < len(sys.argv) and ("-f" == sys.argv[index + 1] or "--force" == sys.argv[index + 1]):
                index += 1
                updateNetwork(targetNetwork, True)
            else:
                updateNetwork(targetNetwork, False)
        else:
            print("Error: To use update option you need set Network name")
            printNetworks()
            exit()
        continue
    elif "help" == command:
        printHelpBlock()
        sys.exit()
    index += 1

