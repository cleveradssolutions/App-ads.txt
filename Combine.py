from functools import total_ordering
import os
import re
import sys
import json
import argparse
from datetime import date

_CERTIFICATIONS_FILE = "CertificationIds.json"
_RESULT_FILE = "app-ads.txt"
_RESULT_FOR_GAMES_FILE = "app-ads-games.txt"
_TEMP_FILE = "TempUpdate.txt"
_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
_NETS_DIR_NAME = "Networks"
_DSP_DIR_NAME = "InternalExchange"
_TYPE_DIRECT = 'DIRECT'
_TYPE_RESELLER = 'RESELLER'


_SOURCES = [
    "GoogleAds",
    "AudienceNetwork",
    "Pangle",
    "IronSource",
    "AppLovin",
    "UnityAds",
    "Mintegral",
    "LiftoffMonetize",
    "SuperAwesome",
    "Kidoz",
    "InMobi",
    "Chartboost",
    "YandexAds",
    "DTExchange",
    "Bigo",
    "CASExchange",
    "DSPExchange",
    "Ogury",
    "Madex",
    "HyprMX",
    "StartIO",
    "Smaato",
]
_SOURCE_DSP = [
    "A4G.txt",
    "AppBroda.txt",
    "Potensus.txt",
    "ReklamUp.txt",
    "QT.txt",
    "AdPixis.txt",
    "PremiumAds.txt",
]
_SOURCE_IN_GAMES = [
    "AdInMo.txt",
    "Gadsme.txt",
]
_NOT_CAS_SOURCES = set(_SOURCE_DSP + _SOURCE_IN_GAMES + ['.DS_Store'])
_BANS = [
    # (Reserved by Network name, Banned domain for other Networks)
    # ("AdMob", "google.com")
]
_VARIABLES = {  # SUPPORTED VARIABLES
    # "contact", # contact information
    # "subdomain", # pointer to a subdomain file
    # "inventorypartnerdomain", # reference is followed to an ads.txt file only (not app-ads.txt)
    # "ownerdomain", # specifies the business domain of the business entity that owns the domain/site/app
    # "managerdomain", # Specifies the business domain of a primary or exclusive monetization partner of the publishers inventory
}
_DOMAIN_PATTERN = re.compile(r"^([a-z0-9-]{1,63}\.)+[a-z]{2,9}\Z")
_ID_PATTERN = re.compile("^[a-zA-Z0-9-_]+$")
_CERTIFICATE_PATTERN = re.compile("^[a-zA-Z0-9]+$")

certificateMap = dict()

arg_parser = argparse.ArgumentParser(
    prog='python Combine.py',
    description=(
        'This script can update App-ads.txt for each Ad Networks and combine all to main file.'),
    epilog='Powered by CAS.AI')

arg_subparsers = arg_parser.add_subparsers()

arg_init = arg_subparsers.add_parser(
    'init', help='Create ' + _TEMP_FILE + ' file to update network configuration.')
arg_init.add_argument('file', action='store_true')
arg_init.add_argument('-l', '--list', action='store_true',
                      help='List of available network names.')
arg_init.set_defaults(network=None, release=False, unique_id=False)

arg_update = arg_subparsers.add_parser(
    'update', help='Check each inventory in ' + _TEMP_FILE + ' with inventories in network file.')
arg_update.add_argument(
    'network', nargs='?', default="", help='The file name with network inventories from `' + _NETS_DIR_NAME + '` directory.')
arg_update.add_argument('-f', '--force', action='store_true',
                        help='Replacing all inventories in the network file.')
arg_update.add_argument('-r', '--release', action='store_true',
                        help='Final ' + _RESULT_FILE + ' file generation.')
arg_update.add_argument('--unique-id', action='store_true',
                        help='Verification of unique certification identifiers for each domain.')
arg_update.add_argument('--no-fill-id', dest='fillCertificate', action='store_false',
                        help='Disable autocomplete of known certification identifiers for each domain.')
arg_update.set_defaults(file=False, release=False)

arg_release = arg_subparsers.add_parser(
    'release', help='Final ' + _RESULT_FILE + ' file generation.')
arg_release.add_argument('-g', '--for-games', dest='games',
                         action='store_true', help='Release App-ads-games.txt for Games.')
arg_release.set_defaults(release=True, file=False,
                         network=None, unique_id=False, fillCertificate=True)

args = arg_parser.parse_args()


def print_warning(warning, inventory):
    print('\033[93m   Warning: ' + warning +
          '\n      ' + inventory + '\033[0m')


def fatal_error(error, inventory=''):
    sys.exit('\033[91m   Error: ' + error + '\n      ' + inventory + '\033[0m')


@total_ordering
class Inventory:
    def __init__(self, line, source):
        self.source = source
        self.domain = None
        self.identifier = None
        self.comment = None
        self.variable = None
        self.type = None
        self.certification = None
        if not line or not line.strip() or line.startswith('/'):
            return
        if line.startswith('#'):
            self.comment = line
            return
        if '=' in line:
            self.variable = line.strip().lower()
            pattern = self.variable.split('=')
            if pattern[0] not in _VARIABLES:
                print_warning("Not supported variable in " + source + ".", line)
                self.variable = None
                return
            if not re.match(_DOMAIN_PATTERN, pattern[1]):
                fatal_error("Invalid domain '" +
                            pattern[1] + "' for variable in " + source, line)
            return
        pattern = line.split(',')
        if len(pattern) != 3 and len(pattern) != 4:
            fatal_error("Invalid pattern in " + source +
                        ". It may only contain 3 or 4 segments.", line)

        self.domain = pattern[0].strip().lower()
        if not re.match(_DOMAIN_PATTERN, self.domain):
            fatal_error("Invalid domain in " + source, line)

        for banDomain in _BANS:
            if source != banDomain[0] and self.domain == banDomain[1]:
                self.domain = None
                return

        self.type = pattern[2].split('#')[0].strip().upper()
        if self.type != _TYPE_RESELLER and self.type != _TYPE_DIRECT:
            fatal_error("Invalid pattern in " + source +
                        ". Must be " + _TYPE_RESELLER + " or " + _TYPE_DIRECT + " only.", line)

        self.identifier = pattern[1].strip()
        if not re.match(_ID_PATTERN, self.identifier):
            fatal_error("Invalid publisher id in " + source, line)

        if len(pattern) == 4:
            certification = pattern[3].split('#')[0].strip().lower()
            if certification:
                self.certification = certification
                if (len(certification) != 9 and len(certification) != 16) or not re.match(_CERTIFICATE_PATTERN, self.certification):
                    if self.domain in certificateMap:
                        self.certification = certificateMap[self.domain]
                        print_warning("Certification authority ID for " +
                                    self.domain + " is " + self.certification, line)
                    else:
                        fatal_error("Certification authority ID is invalid in " + source +
                                    ".\nIt may only contain numbers and lowercase letters, and must be 9 or 16 characters.", line)
                elif self.domain in certificateMap:
                    if not certificateMap[self.domain]:
                        print_warning(
                            "Certification authority ID is should be empty for " + self.domain + " in " + source, line)
                        self.certification = ""
                    elif certificateMap[self.domain] != certification:
                        print_warning("Certification authority ID not mach with " +
                                      certificateMap[self.domain] + " in " + source, line)
                elif args.unique_id:
                    try:
                        readyDomain = certificateMap.values().index(certification)
                        print_warning("Certification authority ID is already taken by " +
                                      (certificateMap.keys()[readyDomain]) + " domain. In " + source, line)
                    except ValueError:
                        certificateMap[self.domain] = certification
                else:
                    print_warning("Add unknown certification: " +
                                  certification + " for " + self.domain, line)
                    certificateMap[self.domain] = certification

    def __eq__(self, other):
        if (isinstance(other, Inventory)
            and self.domain == other.domain
            and self.identifier == other.identifier
            and self.comment == other.comment
                and self.variable == other.variable):
            if self.type != other.type:
                print("One inventory have both relationship in " + self.source +
                      "(" + self.type + ") and " + other.source + "(" + other.type + ")")
                print("   " + other.to_line().strip())

                if self.source == other.source:
                    print("   Only " + _TYPE_DIRECT + " lines are added.")
                    other.type = _TYPE_DIRECT
                    self.type = _TYPE_DIRECT
                elif self.source == 'TempUpdate.txt':
                    print("   Only " + self.type + " lines are added.")
                    other.type = self.type
                elif other.source == 'TempUpdate.txt':
                    print("   Only " + other.type + " lines are added.")
                    self.type = other.type
                else:
                    inputMessage = "   Enter 'D' - to add DIRRECT or 'R' - to add RESELLER: "
                    while True:
                        if sys.version_info[0] < 3:
                            userSelect = raw_input(inputMessage)
                        else:
                            userSelect = input(inputMessage)

                        if userSelect.lower() == 'd':
                            other.type = _TYPE_DIRECT
                            self.type = _TYPE_DIRECT
                            break
                        elif userSelect.lower() == 'r':
                            other.type = _TYPE_RESELLER
                            self.type = _TYPE_RESELLER
                            break
                        else:
                            print("   Invalid input value")
                print()
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
        if self.variable:
            return hash(self.variable)
        if not self.domain:
            return hash("")
        return hash(hash(self.domain) + hash(self.identifier))

    def is_comment(self):
        return self.comment

    def is_empty(self):
        return not self.domain and not self.comment and not self.variable

    def to_line(self, fillCertificate=False):
        if self.comment:
            return self.comment
        if self.variable:
            return self.variable + '\n'
        result = self.domain + ', ' + self.identifier + ', ' + self.type
        if self.certification:
            result += ', ' + self.certification
        elif fillCertificate and self.type != _TYPE_DIRECT and self.domain in certificateMap and certificateMap[self.domain]:
            result += ', ' + certificateMap[self.domain]
        return result + '\n'


def read_certifications():
    path = os.path.join(_ROOT_DIR, _CERTIFICATIONS_FILE)
    if os.path.exists(path):
        with open(path, "r") as file:
            certificateMap.update(json.load(file))


def save_certifications():
    with open(os.path.join(_ROOT_DIR, _CERTIFICATIONS_FILE), "w") as file:
        json.dump(certificateMap, file, indent=2, sort_keys=True)


def release():
    currentDate = date.today().strftime("%b %d, %Y")
    totalLines = "0"

    update_dsp(os.path.join(_ROOT_DIR, _NETS_DIR_NAME, "DSPExchange.txt"), _SOURCE_DSP)
    cas_sources = [f for f in os.listdir(os.path.join(_ROOT_DIR, _DSP_DIR_NAME)) 
                   if f not in _NOT_CAS_SOURCES]
    update_dsp(os.path.join(_ROOT_DIR, _NETS_DIR_NAME, "CASExchange.txt"), cas_sources)

    if args.games == True:
        mainFilePath = os.path.join(_ROOT_DIR, _RESULT_FOR_GAMES_FILE)
    else:
        mainFilePath = os.path.join(_ROOT_DIR, _RESULT_FILE)

    if os.path.exists(mainFilePath):
        with open(mainFilePath, "r") as appAdsFile:
            totalLines = str(sum(1 for _ in appAdsFile) - 1)

    inventorySet = set()
    with open(mainFilePath, 'w') as appAdsFile:
        appAdsFile.write("# CAS.ai Updated " + currentDate + '\n')
        appAdsFile.write("OwnerDomain=cas.ai\n")
        appAdsFile.write("cas.ai, 922e6092, DIRECT\n")
        for source in _SOURCES:
            with open(os.path.join(_ROOT_DIR, _NETS_DIR_NAME, source + ".txt"), 'r') as sourceFile:
                for line in sourceFile:
                    inventory = Inventory(line, source)
                    if not inventory.is_empty() and inventory not in inventorySet:
                        inventorySet.add(inventory)
                        appAdsFile.write(inventory.to_line())
        if args.games == True:
            for source in _SOURCE_IN_GAMES:
                with open(os.path.join(_ROOT_DIR, _DSP_DIR_NAME, source), 'r') as sourceFile:
                    for line in sourceFile:
                        if source.endswith('Raw'):
                            if line.strip() and not line.startswith('#'):
                                appAdsFile.write(line)
                        else:
                            inventory = Inventory(line, source)
                            if not inventory.is_empty() and inventory not in inventorySet:
                                inventorySet.add(inventory)
                                appAdsFile.write(inventory.to_line())

    shiledInfo = {
        "schemaVersion": 1,
        "label": _RESULT_FILE,
        "message": currentDate,
        "color": "orange"
    }

    with open(os.path.join(_ROOT_DIR, "Shield.json"), "w") as shiledFile:
        json.dump(shiledInfo, shiledFile)

    print("Combined " + _RESULT_FILE + " with " + str(len(inventorySet)) +
          " (was " + totalLines + ") inventories for " + str(len(_SOURCES)) + " networks.")


def update_dsp(path, sourceNames):
    newInventories = set()
    for source in sourceNames:
        with open(os.path.join(_ROOT_DIR, _DSP_DIR_NAME, source), 'r') as sourceFile:
            for line in sourceFile:
                inventory = Inventory(line, source)
                if inventory.is_empty() or inventory.is_comment():
                    continue
                newInventories.add(inventory)
    return update_items(path, newInventories, force=False, keepHead=False)

def find_full_file_path(name):
    resultDir = _NETS_DIR_NAME
    file = os.path.join(_ROOT_DIR, resultDir, name)
    if not os.path.exists(file):
        resultDir = _DSP_DIR_NAME
        file = os.path.join(_ROOT_DIR, resultDir, name)
        if not os.path.exists(file):
            file = None
    return file

def update(name, force):
    file = find_full_file_path(name + ".txt")
            
    if not file:
        file = find_full_file_path(select_ad_source(name))
    
    newInventories = set()
    with open(os.path.join(_ROOT_DIR, _TEMP_FILE), 'r') as updateFile:
        for line in updateFile:
            inventory = Inventory(line, _TEMP_FILE)
            if inventory.is_empty() or inventory.is_comment():
                continue
            newInventories.add(inventory)
    return update_items(file, newInventories, force, keepHead=True)


def update_items(netFile, newInventories, force, keepHead):
    duplicate = 0
    fillCertificate = args.fillCertificate
    keepInventories = list()
    inventorySet = set()
    
    networkName = os.path.splitext(os.path.basename(netFile))[0] 
    
    with open(netFile, 'r') as sourceFile:
        for line in sourceFile:
            inventory = Inventory(line, networkName)
            if inventory.is_empty() or inventory.is_comment():
                continue
            if inventory in inventorySet:
                duplicate += 1
                print_warning("Duplicate in " + networkName,
                              inventory.to_line())
                continue
            if keepHead:
                if not keepInventories or keepInventories[0].domain == inventory.domain:
                    keepInventories.append(inventory)
            inventorySet.add(inventory)

    diffInventories = newInventories - inventorySet

    if not force and len(diffInventories) == 0 and duplicate == 0:
        print("No found inventories to update for " + networkName)
        return False

    print("Update " + networkName + " inventories")
    for inventory in keepInventories:
        sys.stdout.write("[Keep] " + inventory.to_line())

    for index, inventory in enumerate(diffInventories):
        sys.stdout.write("[New " + str(index) + "] " + inventory.to_line())

    inputMessage = "- Y (yes) - to add new inventories\n- F (force) - to remove obsolute inventories\n- N (no) - to exit\nEnter: "
    if force:
        userSelect = 'f'
    elif sys.version_info[0] < 3:
        userSelect = raw_input(inputMessage)
    else:
        userSelect = input(inputMessage)

    if userSelect.lower() == 'f':
        force = True
    else:
        newInventories.update(inventorySet)

    if force or userSelect.lower() == 'y':
        with open(netFile, 'w') as sourceFile:
            sourceFile.write("#=== " + networkName + " " +
                             date.today().strftime("%b %d, %Y") + '\n')
            for inventory in sorted(keepInventories):
                sourceFile.write(inventory.to_line())
                newInventories.discard(inventory)

            # result = list(newInventories)
            # result.sort()
            for inventory in sorted(newInventories):
                sourceFile.write(inventory.to_line(fillCertificate))

        print("Updated " + networkName + " with " +
              str(len(newInventories) + len(keepInventories)) + " inventories.")
        return True
    return False

def select_ad_source(filter):
    all_files = []

    for f in _SOURCES:
        if not filter or filter.lower() in f.lower():
            all_files.append(f + ".txt")

    for f in os.listdir(os.path.join(_ROOT_DIR, _DSP_DIR_NAME)):
        if f.endswith('.txt'):
            if not filter or filter.lower() in f.lower():
                all_files.append(f)

    if not all_files:
        return select_ad_source(None)
    
    if len(all_files) == 1:
        return all_files[0]    
    
    columns = 3
    col_width = 30
    rows = (len(all_files) + columns - 1) // columns  # Количество строк

    for row in range(rows):
        line = ""
        for col in range(columns):
            idx = col * rows + row
            if idx < len(all_files):
                item = all_files[idx]
                line += f"{idx+1:3}: {item:<{col_width}}"
        print(line)
        
    while True:
        try:
            choice = int(input("Enter ad source index: "))
            if 1 <= choice <= len(all_files):
                selected_file = all_files[choice - 1]
                return selected_file
            else:
                print_warning("Index not found. Try again.")
        except ValueError:
            print_warning("Please enter just number.")

if args.file == True:
    open(os.path.join(_ROOT_DIR, _TEMP_FILE), 'w+').close()
    print('File ' + _TEMP_FILE + ' created')

    if args.list == True:
        print("Available networks: " + ", ".join(_SOURCES))
else:
    read_certifications()

if args.network is not None:
    update(args.network, args.force)

if args.release == True:
    release()

if args.file == False:
    save_certifications()
