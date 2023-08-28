import os
import sys
import json
import argparse
from datetime import date


arg_parser = argparse.ArgumentParser(
        prog='python Combine.py',
        description=(
            'This script can update App-ads.txt for each Ad Networks and combine all to main file.'),
        epilog='Powered by CAS.AI')

arg_subparsers = arg_parser.add_subparsers()

arg_init = arg_subparsers.add_parser('init', help='Create TempUpdate.txt file to update network configuration.')
arg_init.add_argument('file', action='store_true')
arg_init.add_argument('-l', '--list', action='store_true', help='List of available network names.')
arg_init.set_defaults(network=None, release=False, unique_id=False)

arg_update = arg_subparsers.add_parser('update', help='Check each inventory in TempUpdate.txt with inventories in network file.')
arg_update.add_argument('network', help='The file name with network inventories from `Networks` directory.')
arg_update.add_argument('-f', '--force', action='store_true', help='Replacing all inventories in the network file.')
arg_update.add_argument('-r', '--release', action='store_true', help='Final App-ads.txt file generation.')
arg_update.add_argument('--unique-id', action='store_true', help='Verification of unique certification identifiers for each domain.')
arg_update.add_argument('--no-fill-id', dest='fillCertificate', action='store_false', help='Disable autocomplete of known certification identifiers for each domain.')
arg_update.set_defaults(file=False)

arg_release = arg_subparsers.add_parser('release', help='Final App-ads.txt file generation.')
arg_release.add_argument('release', action='store_true')
arg_release.set_defaults(file=False, network=None, unique_id=False)

args = arg_parser.parse_args()

def print_warning(str):
    print('\033[93m   Warning: ' + str + '\033[0m')

def fatal_error(error):
    sys.exit('\033[91m   Error: ' + error + '\033[0m')

rootDir = os.path.dirname(os.path.abspath(__file__))
sources = [ 
    "CASExchange.txt",
    "GoogleAds.txt",
    "AudienceNetwork.txt",
    "AdColony.txt",
    "Pangle.txt",
    "IronSource.txt",
    "AppLovin.txt",
    "UnityAds.txt",
    "Mintegral.txt",
    "LiftoffMonetize.txt",
    "SuperAwesome.txt",
    "Kidoz.txt",
    "InMobi.txt",
    "myTarget.txt",
    "Chartboost.txt", 
    "YandexAds.txt",
    "DTExchange.txt",
    #"Others.txt",
    #Deprecated:
    #Smaato.txt,
    #StartIo.txt,
]
bannedDomains = [
    # (Reserved by Network name, Banned domain for other Networks)
    #("AdMob", "google.com")
]
inventorySet = dict()
certificateMap = dict()
certificateInvalidMap = set()

def is_domain_allowed(line, source):
    for domain in bannedDomains:
        if source != domain[0] and line.startswith(domain[1]):
            return False
    return True

def convert_to_unique(line, source):
    if not line or not line.strip() or line.startswith('/'):
        return ("", None)
    if line.startswith('#'):
        return (line, None)
    pattern = line.split(',')
    if len(pattern) != 3 and len(pattern) != 4:
        fatal_error("Invalid pattern in " + source + ". It may only contain 3 or 4 segments.\n" + line)

    accountType = pattern[2].strip().upper()
    if accountType != 'RESELLER' and accountType != 'DIRECT':
        fatal_error("Invalid pattern in " + source + ". Must be RESELLER or DIRECT only.\n" + line)

    domainName = pattern[0].strip().lower()
    publisherId = pattern[1].strip().lower()
    result = domainName + ', ' + publisherId + ', ' + accountType

    if len(pattern) == 4:
        endOfLine = pattern[3].split('#')
        certificationId = endOfLine[0].strip().lower()
        if certificationId:
            if len(certificationId) != 9 and len(certificationId) != 16:
                fatal_error("Certification authority ID is invalid in " + source + ". It may only contain numbers and lowercase letters, and must be 9 or 16 characters.\n" + line)
                return (result, None)
            if domainName in certificateMap:
                if certificateMap[domainName] != certificationId:
                    print_warning("Certification authority ID not mach with " + certificateMap[domainName] + " in " + source + ". All certificate ids will be removed for folowing domain.\n" + line)
                    certificateInvalidMap.add(domainName)
            else:
                if args.unique_id:
                    try:
                        readyDomain = certificateMap.values().index(certificationId)
                        print_warning("Certification authority ID is already taken by " + 
                                (certificateMap.keys()[readyDomain]) + " domain. In " + source + ":\n" + line)
                    except ValueError:
                        certificateMap[domainName] = certificationId
                else:
                    certificateMap[domainName] = certificationId
            return (result, certificationId)

    return (result, None)

def convert_for_file(line):
    if line.startswith('#'):
        return line
    domain = line.split(',')[0].strip()
    if domain not in certificateInvalidMap and domain in certificateMap:
        line +=  ', ' + certificateMap[domain]
    return line + '\n'

def convert_for_file(line, certificate):
    if line.startswith('#'):
        return line
    if certificate:
        line +=  ', ' + certificate
    return line + '\n'

def release():
    currentDate = date.today().strftime("%b %d, %Y")
    totalLines = "0"

    with open(rootDir + "/app-ads.txt", "rbU") as appAdsFile:
        totalLines = str(sum(1 for _ in appAdsFile) - 1)

    with open(rootDir + "/app-ads.txt", 'w+') as appAdsFile:
        appAdsFile.write("# CAS.ai Updated " + currentDate + ', support@cleveradssolutions.com\n')
        for source in sources:
            with open(rootDir + "/Networks/" + source, 'r') as sourceFile:
                for line in sourceFile:
                    line, certificate = convert_to_unique(line, source)
                    if line and line not in inventorySet:
                        inventorySet[line] = certificate
                        appAdsFile.write(convert_for_file(line, certificate))
            
    shiledInfo = {
        "schemaVersion": 1,
        "label": "App-ads.txt",
        "message": currentDate,
        "color": "orange"
    }

    with open(rootDir + "/Shield.json", "w") as shiledFile:
        json.dump(shiledInfo, shiledFile)

    print("Combined App-ads.txt with " + str(len(inventorySet)) + " (was " + totalLines + ") inventories for " + str(len(sources)) + " networks.")

def update(networkName, force):
    tempFileName = 'TempUpdate.txt'
    duplicate = 0
    foundNews = False
    keepDomain = None
    fillCertificate = args.fillCertificate
    keepInventories = dict()
    newInventories = dict()

    with open(rootDir + "/Networks/" + networkName + ".txt", 'r') as sourceFile:
        for line in sourceFile:
            line, certificate = convert_to_unique(line, networkName)
            if not line or line.startswith('#'):
                continue
            if line in inventorySet:
                duplicate += 1
                print("Duplicate in source: " + line[:-1])
                continue
            if not keepDomain:
                keepDomain = line.split(',')[0]
            if line.startswith(keepDomain):
                keepInventories[line] = certificate
            inventorySet[line] = certificate

    if force:
        certificateMap.clear()

    with open(rootDir + "/" + tempFileName, 'r') as updateFile:
        for line in updateFile:
            line, certificate = convert_to_unique(line, tempFileName)
            if not line or line.startswith('#'):
                continue
            if line and is_domain_allowed(line, networkName):
                newInventories[line] = certificate
                if line not in inventorySet:
                    print("New inventory:\n" + line)
                    foundNews = True


    if not force and not foundNews and duplicate == 0 and len(newInventories) <= len(inventorySet):
        print("No found inventories to update.")
        return False
    if force:
        userSelect = 'f'
    elif sys.version_info[0] < 3:
        userSelect = raw_input("Enter Y (to add new inventories), F (to force remove obsolute inventories) or N (to exit): ")
    else:
        userSelect = input("Enter Y (to add new inventories), F (to force remove obsolute inventories) or N (to exit): ")
        
    if userSelect.lower() == 'f':
        force = True
    else:
        newInventories.update(inventorySet)

    if force or userSelect.lower() == 'y':
        with open(rootDir + "/Networks/" + networkName + ".txt", 'w') as sourceFile:
            sourceFile.write("#=== " + networkName + " " + date.today().strftime("%b %d, %Y") + '\n')
            for line, certificate in keepInventories:
                sourceFile.write(convert_for_file(line, certificate))
                newInventories.pop(line, None)

            result = list(newInventories.keys())
            result.sort()
            for line in result:
                if not is_domain_allowed(line, networkName):
                    continue
                if fillCertificate:
                    sourceFile.write(convert_for_file(line))
                else:
                    sourceFile.write(convert_for_file(line, newInventories[line]))

        print("Updated " + networkName + " with " + str(len(result) + len(keepInventories)) + " inventories.")
        return True
    return False

if args.file == True:
    open(rootDir + "/TempUpdate.txt", 'w+').close()
    print('File TempUpdate.txt created')

    if args.list == True:
        print("Available networks: " + ", ".join(map(lambda net: os.path.splitext(net)[0], sources)))


if args.network is not None:
    if update(args.network, args.force) and args.release:
        release()

if args.release is True:
    release()
