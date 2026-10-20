# ---------------------------------------------------------------- files and folders
NETWORKS_DIR = "Networks"            # big networks
EXCHANGE_DIR = "InternalExchange"    # DSPs / exchanges
TEMP_FILE = "TempUpdate.txt"         # input of `update`
HEADS_FILE = "domains.json"          # head domain(s) of every network
CERT_FILE = "CertificationIds.json"  # known certification ids: domain -> id ("" = domain must have none)
DRIVE_DIR = "GoogleDrive"            # default input folder of `drive`
TABLES_DIR = "Tables"                # default input folder of `table`

# ---------------------------------------------------------------- special networks
# Built by `release` from InternalExchange; never edited by hand.
GENERATED = {"CASExchange", "DSPExchange"}

# Copied as-is (no validation, no sorting); only the header date is ours.
RAW = {"Gadsme"}

# Updated by adding lines: obsolete lines are kept (the network gives its lines in parts).
MERGE = {"Bigo"}

# ---------------------------------------------------------------- line rules
# Lines of these domains are skipped everywhere (input files and existing network files).
BANNED_DOMAINS = {
    "liftoff.io",  # deprecated LiftoffMonetize domain
}
# Supported `name=value` lines; others are skipped with a warning.
VARIABLES = {"inventorypartnerdomain"}

# ---------------------------------------------------------------- release
# Networks/ files included in the final file, in this order.
RELEASE_NETWORKS = [
    "GoogleAds", "AudienceNetwork", "Pangle", "IronSource", "AppLovin", "UnityAds", "Mintegral",
    "LiftoffMonetize", "SuperAwesome", "Kidoz", "Prado", "InMobi", "Chartboost", "YangoAds",
    "DTExchange", "Bigo", "CASExchange", "DSPExchange", "Ogury", "Madex", "Maticoo", "HyprMX",
    "StartIO", "Verve", "Monetrix", "DisplayIO", "Bidease", "BlueSea", "BidMachine"
]

# InternalExchange/ files collected into DSPExchange. All the other exchanges go to CASExchange.
DSP_POOL = ["AppBroda", "Potensus", "AdPixis", "Adyugo", "PremiumAds", "Reklamup", "AdsYield", "VoiseTech"]

# InternalExchange/ files added as-is to the games and partner files only (never to the public file).
GAMES_ONLY = ["Gadsme"]

# release target -> (output file, lines after the "# CAS.ai Updated <date>" header)
RELEASE_TARGETS = {
    "main": ("app-ads.txt", ["OwnerDomain=cas.ai", "cas.ai, 922e6092, DIRECT"]),
    "games": ("app-ads-games.txt", ["OwnerDomain=cas.ai", "cas.ai, 922e6092, DIRECT"]),
    "partner": ("app-ads-partner.txt", ["OwnerDomain=psvgamestudio.com"]),
}

# The partner file drops CASExchange and every record whose domain contains this text.
PARTNER_EXCLUDE = "cas.ai"