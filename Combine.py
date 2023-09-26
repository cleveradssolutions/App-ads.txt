from functools import total_ordering
import os
import re
import sys
import json
import argparse
from datetime import date

rootDir = os.path.dirname(os.path.abspath(__file__))

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
    "HyprMX.txt",
    "Smaato.txt"
]
bannedDomains = [
    # (Reserved by Network name, Banned domain for other Networks)
    #("AdMob", "google.com")
]
domainPattern = re.compile("^((?!-)[A-Za-z0-9-]" + "{1,63}(?<!-)\\.)" + "+[A-Za-z]{2,6}")
inventorySet = set()
certificateMap = dict()

def print_warning(warning, inventory):
    print('\033[93m   Warning: ' + warning + '\n      ' + inventory + '\033[0m')

def fatal_error(error, inventory):
    sys.exit('\033[91m   Error: ' + error + '\n      ' + inventory + '\033[0m')


@total_ordering
class Inventory:
    def __init__(self, line, source):
        self.source = source
        self.domain = None
        self.identifier = None
        self.comment = None
        self.certification = None
        if not line or not line.strip() or line.startswith('/'):
            return
        if line.startswith('#'):
            self.comment = line
            return
        pattern = line.split(',')
        if len(pattern) != 3 and len(pattern) != 4:
            fatal_error("Invalid pattern in " + source + ". It may only contain 3 or 4 segments.", line)

        self.domain = pattern[0].strip().lower()
        if not re.search(domainPattern, self.domain):
            fatal_error("Invalid domain in " + source, line)
        
        for banDomain in bannedDomains:
            if source != banDomain[0] and self.domain == banDomain[1]:
                self.domain = None
                return
            
        self.type = pattern[2].split('#')[0].strip().upper()
        if self.type != 'RESELLER' and self.type != 'DIRECT':
            fatal_error("Invalid pattern in " + source + ". Must be RESELLER or DIRECT only.", line)

        self.identifier = pattern[1].strip().lower()

        if len(pattern) == 4:
            certification = pattern[3].split('#')[0].strip().lower()
            if certification:
                self.certification = certification
                if len(certification) != 9 and len(certification) != 16:
                    if self.domain in certificateMap:
                        fatal_error("Certification authority ID for " + self.domain + " is " + certificateMap[self.domain], line)
                    else:    
                        fatal_error("Certification authority ID is invalid in " + source + ".\nIt may only contain numbers and lowercase letters, and must be 9 or 16 characters.", line)
                elif self.domain in certificateMap:
                    if certificateMap[self.domain] != certification:
                        print_warning("Certification authority ID not mach with " + certificateMap[self.domain] + " in " + source, line)
                elif args.unique_id:
                    try:
                        readyDomain = certificateMap.values().index(certification)
                        print_warning("Certification authority ID is already taken by " + 
                                (certificateMap.keys()[readyDomain]) + " domain. In " + source, line)
                    except ValueError:
                        certificateMap[self.domain] = certification
                else:
                    certificateMap[self.domain] = certification

    def __eq__(self, other):
        if (isinstance(other, Inventory)
            and self.domain == other.domain 
            and self.identifier == other.identifier
            and self.comment == other.comment):
            if self.type != other.type:
                print_warning("Relationship is already set " + self.type + " by " + self.source + 
                              "\nPlease fix conflict with " + other.source, other.to_line())
            return True
        return False

    def __lt__(self, other):
        if not isinstance(other, Inventory):
            return NotImplemented
        if self.domain != other.domain:
            return self.domain < other.domain
        if self.type != other.type:
            return self.type < other.type
        return self.identifier < other.identifier

    def __hash__(self):
        if self.comment:
            return hash(self.comment)
        if not self.domain:
            return hash("")
        return hash(hash(self.domain) + hash(self.identifier))
    
    def is_comment(self):
        return self.comment
    
    def is_empty(self):
        return not self.domain and not self.comment
    
    def to_line(self, fillCertificate=False):
        if self.comment:
            return self.comment
        result = self.domain + ', ' + self.identifier + ', ' + self.type
        if self.certification:
            result += ', ' + self.certification
        elif fillCertificate and self.domain in certificateMap:
            result += ', ' + certificateMap[self.domain]
        return result + '\n'

def read_certifications():
    path = rootDir + "/CertificationIds.json"
    if os.path.exists(path):
        with open(path, "r") as file:
            certificateMap.update(json.load(file))

def save_certifications():
    with open(rootDir + "/CertificationIds.json", "w+") as file:
        json.dump(certificateMap, file, indent=2, sort_keys=True)

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
                    inventory = Inventory(line, source)
                    if not inventory.is_empty() and inventory not in inventorySet:
                        inventorySet.add(inventory)
                        appAdsFile.write(inventory.to_line())
            
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
    keepInventories = set()
    newInventories = set()

    with open(rootDir + "/Networks/" + networkName + ".txt", 'r') as sourceFile:
        for line in sourceFile:
            inventory = Inventory(line, networkName)
            if inventory.is_empty() or inventory.is_comment():
                continue
            if inventory in inventorySet:
                duplicate += 1
                print_warning("Duplicate in " + networkName, inventory.to_line())
                continue
            if not keepDomain:
                keepDomain = inventory.domain
            if inventory.domain == keepDomain:
                keepInventories.add(inventory)
            inventorySet.add(inventory)

    with open(rootDir + "/" + tempFileName, 'r') as updateFile:
        for line in updateFile:
            inventory = Inventory(line, tempFileName)
            if inventory.is_empty() or inventory.is_comment():
                continue
            newInventories.add(inventory)
            if inventory not in inventorySet:
                print("New inventory:\n   " + inventory.to_line())
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
            for inventory in sorted(keepInventories):
                sourceFile.write(inventory.to_line())
                newInventories.discard(inventory)

            #result = list(newInventories)
            #result.sort()
            for inventory in sorted(newInventories):
                sourceFile.write(inventory.to_line(fillCertificate))

        print("Updated " + networkName + " with " + str(len(newInventories) + len(keepInventories)) + " inventories.")
        return True
    return False

if args.file == True:
    open(rootDir + "/TempUpdate.txt", 'w+').close()
    print('File TempUpdate.txt created')

    if args.list == True:
        print("Available networks: " + ", ".join(map(lambda net: os.path.splitext(net)[0], sources)))
else:
    read_certifications()

if args.network is not None:
    if update(args.network, args.force) and args.release:
        release()

if args.release is True:
    release()

if args.file == False:
    save_certifications()
