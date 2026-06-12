"""
Plexis SGP v4 — Stage 1b.2a: name-keyword classifier for Other/Uncategorized residue.

Runs regex-based rules on name + address to assign plexis_category.
Rules are ordered; first match wins. Returns None if no rule fires.
"""
from __future__ import annotations
import re
from typing import Optional

# (category, regex) — evaluated top-down on name (or name+" "+address)
RULES: list[tuple[str, re.Pattern]] = [
    # Religious — strong signals
    ("religious_worship", re.compile(r"\b(church|chapel|cathedral|parish|methodist|anglican|catholic|assembly of god|baptist|tabernacle|mission|gospel)\b", re.I)),
    ("religious_worship", re.compile(r"\b(temple|monastery|shrine|pagoda|lian hwa|kwan im)\b", re.I)),
    ("religious_worship", re.compile(r"\b(masjid|mosque|madrasah|musallah)\b", re.I)),
    ("religious_worship", re.compile(r"\b(gurdwara|sikh|hindu mandir|mandir)\b", re.I)),
    ("religious_worship", re.compile(r"\b(synagogue|jewish)\b", re.I)),

    # Residential — HDB blocks, MSCPs, condos
    ("residential", re.compile(r"\bmscp\b", re.I)),  # multi-storey carpark but tied to residential blocks
    ("residential", re.compile(r"^(blk|block)\s+\d+[a-z]?\b", re.I)),
    ("residential", re.compile(r"\b(service\s+apartments?|service\s+residences?|serviced\s+apartments?)\b", re.I)),
    ("residential", re.compile(r"\b(cluster\s+house|cluster\s+home|townhouse|semi-detached|bungalow)\b", re.I)),
    ("residential", re.compile(r"\b(apartments?|residence|residences|mansion|manor|court|villa)s?\b", re.I)),
    ("residential", re.compile(r"\bcondo(minium)?\b", re.I)),

    # Education
    ("education", re.compile(r"\b(academy|institute|school|education|training\s+centre|kindergarten|montessori|tuition|learning\s+centre)\b", re.I)),
    ("education", re.compile(r"\b(university|polytechnic|college|ite\b)", re.I)),

    # Health & medical
    ("health_medical", re.compile(r"\b(clinic|medical|dental|dentist|surgery|hospital|pharmacy|pharma|physiotherapy|polyclinic|aesthetic|wellness\s+clinic|tcm)\b", re.I)),
    ("health_medical", re.compile(r"\b(veterinary|vet\s+clinic|animal\s+clinic)\b", re.I)),

    # Hawker / restaurant keywords (SGP-specific foods)
    ("hawker", re.compile(r"\b(hawker|kopitiam|koufu|food\s+court|food\s+centre|coffee\s+shop)\b", re.I)),
    ("restaurant", re.compile(r"\b(porridge|nasi|chicken\s+rice|bak\s+kut\s+teh|laksa|char\s+kway\s+teow|teh\s+tarik|dim\s+sum|hainanese|teochew|peranakan|cantonese|shabu|hotpot|izakaya|ramen|sushi|yakiniku|pho|bistro|trattoria|osteria|parrilla|churrasco|casa\s+de\s+comidas)\b", re.I)),
    ("restaurant", re.compile(r"\b(restaurant|seafood|eatery|kitchen|diner)\b", re.I)),
    ("bakery", re.compile(r"\b(bakery|boulangerie|patisserie|cake\s+shop|bread\s+shop)\b", re.I)),
    ("cafe_coffee", re.compile(r"\b(cafe|café|coffee|espresso|roaster|bubble\s+tea|boba)\b", re.I)),
    ("bar_nightlife", re.compile(r"\b(bar|pub|taproom|wine\s+bar|lounge|nightclub|speakeasy|brewery)\b", re.I)),

    # Fitness & rec
    ("fitness_recreation", re.compile(r"\b(gym|fitness|yoga|pilates|crossfit|martial\s+arts|boxing\s+gym|mma|dojo)\b", re.I)),
    ("fitness_recreation", re.compile(r"\b(football\s+field|basketball\s+court|tennis\s+court|swimming\s+pool|stadium|sports\s+hall|recreation\s+centre)\b", re.I)),

    # Parks / nature
    ("park_open", re.compile(r"\b(reservoir|nature\s+reserve|fishing\s+ground|park\s+connector|wetland)\b", re.I)),
    ("park_open", re.compile(r"\b(garden|park|playground|green)\b", re.I)),

    # Convenience / retail patterns
    ("convenience", re.compile(r"\b(24/7|24\s+hours?|vending\s+machine|ijooz|atm|parcel\s+locker|pick\s+locker)\b", re.I)),
    ("shopping_retail", re.compile(r"\b(jewellery|jewelry|boutique|optical|apparel\s+store|fashion|florist)\b", re.I)),
    ("shopping_retail", re.compile(r"\b(furniture|hardware|electronics\s+store|appliance|bookstore|book\s+shop)\b", re.I)),
    ("supermarket", re.compile(r"\b(supermarket|hypermarket|ntuc|fairprice|cold\s+storage|giant|sheng\s+siong|prime|jason|don\s+don\s+donki|don\s+don|donki)\b", re.I)),

    # Hotels
    ("hotel_hospitality", re.compile(r"\b(hotel|resort|hostel|inn|bed\s+and\s+breakfast|b&b|chalet)\b", re.I)),

    # Fast food
    ("fast_food", re.compile(r"\b(mcdonalds?|kfc|burger\s+king|subway|pizza\s+hut|domino|popeye|jollibee|wendy)\b", re.I)),

    # Beauty & personal
    ("beauty_personal", re.compile(r"\b(salon|spa|massage|nail|hair|barber|beauty|skin\s+care|skincare|brow|lash)\b", re.I)),
    ("beauty_personal", re.compile(r"\b(tailor|alteration|dressmaker)\b", re.I)),

    # Services (broad)
    ("services", re.compile(r"\b(employment|maid\s+agency|cleaning|laundry|dry\s+clean|key\s+cutting|locksmith|plumb|electrician|aircon|handyman|mover)\b", re.I)),
    ("services", re.compile(r"\b(agency|consult(ant|ing)?|marketing|pr\s+firm|advertising|branding|design\s+studio|creative)\b", re.I)),
    ("services", re.compile(r"\b(law\s+firm|lawyer|solicitor|advocate|attorney|legal|law\s+office)\b", re.I)),
    ("services", re.compile(r"\b(accounting|audit|bookkeep|tax|cpa)\b", re.I)),
    ("services", re.compile(r"\b(real\s+estate|property|propnex|eranz|eraco|era\s+realty|realtor)\b", re.I)),
    ("services", re.compile(r"\b(car\s+wash|workshop|auto\s+repair|garage|mechanic)\b", re.I)),
    ("services", re.compile(r"\b(pet\s+groom|pet\s+hotel|pet\s+services|dog\s+day\s+care)\b", re.I)),
    ("services", re.compile(r"\b(funeral|casket|undertaker|crematori|wake)\b", re.I)),
    ("services", re.compile(r"\b(courier|delivery|logistics|freight|fulfillment)\b", re.I)),
    ("services", re.compile(r"\b(travel\s+agency|tour\s+operator|dmc|travel\s+services)\b", re.I)),

    # Transportation
    ("transportation", re.compile(r"\b(bus\s+stop|bus\s+station|bus\s+interchange|mrt\s+station|lrt\s+station|taxi\s+stand|carpark|car\s+park|ferry|jetty|terminal|airport|charging\s+station|petrol\s+station|gas\s+station|bridge)\b", re.I)),
    ("transportation", re.compile(r"\b(ev\s+charging|sp\s+mobility|charge\+|bluesg|shell\s+recharge)\b", re.I)),
    ("transportation", re.compile(r"^[^a-z]*\b(whitley|newton|jurong|tuas|clementi|bedok|tampines|yishun|sengkang|punggol|bishan|hougang|toa\s+payoh|serangoon|marine|changi|pioneer|kallang)\s+(rd|road|street|st|ave|avenue|blvd|boulevard|way|drive|dr|lane|ln|link|close)\b", re.I)),

    # Government & public
    ("government_public", re.compile(r"\b(post\s+office|fire\s+station|police\s+station|embassy|consulate|library|community\s+club|cc\s+centre|residents'?\s+committee)\b", re.I)),
    ("government_public", re.compile(r"\b(ministry|hdb|ura|lta|nea|singpost|icayw|cpf|iras|mom|singapore\s+customs)\b", re.I)),

    # Entertainment
    ("entertainment_culture", re.compile(r"\b(museum|art\s+gallery|cinema|performing\s+arts|theatre|theater|concert\s+hall|exhibition|cultural\s+centre)\b", re.I)),
    ("entertainment_culture", re.compile(r"\b(tourist\s+attraction|viewpoint|landmark|heritage\s+site|zoo|aquarium)\b", re.I)),

    # Industrial (broad — placed late to not catch "construction aesthetics")
    ("industrial_mfg", re.compile(r"\b(manufacturer|manufacturing|wholesal|industrial\s+supplier|construction\s+company|constructions|builder|civil\s+engineering\s+contract|contractor)\b", re.I)),
    ("industrial_mfg", re.compile(r"\b(marine\s+consult|marine\s+services|shipyard|drydock|port\s+operator)\b", re.I)),
    ("industrial_mfg", re.compile(r"\b(warehouse|freight\s+forward|import\s+export|trading\s+co)\b", re.I)),
    ("industrial_mfg", re.compile(r"\b(car\s+dealer|auto\s+dealer|motor\s+trading)\b", re.I)),

    # Business / office — Pte Ltd / Corp generic (placed late to not over-claim)
    ("business_office", re.compile(r"\b(pte\.?\s*ltd|pte\s+limited|p\.t\.e|private\s+limited)\b", re.I)),
    ("business_office", re.compile(r"\b(holdings|corporation|corp\.|inc\.|incorporated|llp|llc)\b", re.I)),
    ("business_office", re.compile(r"\b(coworking|shared\s+office|serviced\s+office|virtual\s+office)\b", re.I)),
    ("business_office", re.compile(r"\b(bank\b|dbs|ocbc|uob|maybank|hsbc|citibank|standard\s+chartered|hong\s+leong)\b", re.I)),
    ("business_office", re.compile(r"\b(insurance|prudential|aviva|ntuc\s+income|aia|great\s+eastern|allianz)\b", re.I)),

    # ---------- Pass-2 catch-ups (learned from residue inspection) ----------
    # Health / wellness
    ("health_medical", re.compile(r"\b(healthcare|health\s+care|rehabilitation|rehab|physio|occupational\s+therapy|speech\s+therapy|tcm\s+hall|chiropractic|podiatry|psychology|counsell?ing\s+centre|ihh)\b", re.I)),

    # Retail variants
    ("shopping_retail", re.compile(r"\b(houseware|houseworks|home\s+store|aromatherapy|essential\s+oils|fragrance|scent|perfume|vape\s+shop|tobacconist|jewell?er|goldsmith)\b", re.I)),
    ("shopping_retail", re.compile(r"\b(outlet|shop|store)$", re.I)),
    ("shopping_retail", re.compile(r"\b(floor(ing)?|vinyl|parquet|tile|laminate|carpet|wallpaper|curtain|rug)\b", re.I)),
    ("shopping_retail", re.compile(r"\b(koi\s+farm|fish\s+farm|orchid\s+farm|aquarium\s+shop|pet\s+shop)\b", re.I)),

    # Services catch-ups
    ("services", re.compile(r"\b(repair|fix|service\s+centre)\b", re.I)),
    ("services", re.compile(r"\b(air[- ]?con(ditioning)?|aircon|hvac)\b", re.I)),
    ("services", re.compile(r"\b(auto|motor|car\s+service)\b", re.I)),
    ("services", re.compile(r"\b(rescue|dropoff|drop\s+off|pickup|collection\s+point)\b", re.I)),
    ("services", re.compile(r"\b(studios?|atelier)\b", re.I)),   # broad — art/design/music studios
    ("services", re.compile(r"\b(enterprise|enterprises)\b", re.I)),  # sole-proprietor style

    # Transportation catch-ups
    ("transportation", re.compile(r"\b(bus\s+depot|depot|circuit|mrt\s+exit|lrt\s+exit|stn\s+exit|exit\s+[a-z]\b)\b", re.I)),
    ("transportation", re.compile(r"\b(singapore\s+airlines|sia|air\s+china|cathay|scoot|jetstar|airasia|qantas|emirates|qatar\s+airways|klm)\b", re.I)),

    # Hotels catch-ups (branded)
    ("hotel_hospitality", re.compile(r"\b(heritage\s+collection|boutique\s+hotel|marriott|hyatt|hilton|shangri-?la|mandarin|conrad|fullerton|fairmont|accor|ibis|holiday\s+inn|oakwood|pan\s+pacific|capella|rosewood|four\s+seasons|intercontinental)\b", re.I)),

    # Address-only (road / block with no venue) -> transportation (street infra)
    ("transportation", re.compile(r"^[^a-z0-9]*(?:[0-9]+[a-z]?\s+)?[a-z][a-z\s\']+(?:rd|road|street|st|ave|avenue|blvd|boulevard|way|drive|dr|lane|ln|link|close|loop|cres|crescent|walk|terrace|ter|quay|park\s+road)\s*$", re.I)),
    ("transportation", re.compile(r"^[0-9]+[a-z]?\s+[A-Z]", re.I)),  # pure "690 S Woodlands Dr" patterns via the above rule
]


def classify_by_name(name: str, address: Optional[str] = None) -> Optional[str]:
    if not name:
        return None
    text = name
    if address:
        text = f"{name}  {address}"
    for cat, rx in RULES:
        if rx.search(text):
            return cat
    return None
