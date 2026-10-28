"""Beliefs, 2026-10-28. An idea is what people believe; the joke is only the packaging (register).

Each post keeps its concept (the first, packaging-led tagging) and gets a belief and a stance:
  supports  the post pushes the belief (a joke, an argument, a testimony)
  attacks   the post pushes against it (a debunk, a statistic, a counter-joke)
  neutral   explainer, question or applause with no position on the belief

Test for every belief label: (1) someone can say "I believe that ..."; (2) a joke, a serious post and a
debunk can all be about it; (3) one post can support it and another attack it; (4) no packaging word.
X01 and X02 fail test 1 on purpose: they hold posts with no belief and stay off the rope.
"""

BELIEFS = {
    "B01": "Don't use our manga for your riots",
    "B02": "The Japanese are perverts",
    "B03": "The Japanese are suicidal",
    "B04": "The Japanese are submissive",
    "B05": "The French are cowards",
    "B06": "Japan never paid for its war",
    "B07": "It's a Muslim invasion",
    "B08": "The rioters are not real French",
    "B09": "The protesters are just looters",
    "B10": "France is collapsing",
    "B11": "The media hide the truth",
    "B12": "The Japanese are racist",
    "B13": "Japan's kindness is a facade",
    "B14": "Japan started it",
    "B15": "France won the meme war",
    "B16": "Nobody beats the French at trolling",
    "B17": "The whole world is against Japan",
    "B18": "Auto-translation turned X into a battlefield",
    "X01": "No belief: why are they fighting?",
    "X02": "No belief: racial insult",
}

# Camp whose voice the belief serves. "ALL" = no camp owns it (every side can support it).
OWNER = {"B01": "JA", "B02": "FR", "B03": "FR", "B04": "FR", "B05": "JA", "B06": "FR", "B07": "JA", "B08": "JA",
         "B09": "JA", "B10": "JA", "B11": "JA", "B12": "FR", "B13": "FR", "B14": "FR", "B15": "FR", "B16": "FR",
         "B17": "FR", "B18": "ALL", "X01": None, "X02": None}

# Default belief of each first-pass concept.
FROM_CONCEPT = {"K01": "B01", "K02": "B01", "K23": "B01", "K03": "B02", "K04": "B03", "K05": "B04", "K06": "B06",
                "K07": "B07", "K08": "B07", "K10": "B08", "K13": "B09", "K12": "B10", "K09": "B11", "K18": "B11",
                "K11": "B12", "K16": "B13", "K19": "B14", "K14": "B15", "K20": "B16", "K15": "B18", "K22": "B18",
                "K17": "B17", "K21": "X01"}

# Per-post belief changes (the concept mixed two beliefs).
BELIEF = {
    # The bomb and WWII: Japanese-side posts call the French cowards; "Little Boy" jokes are pedophilia jokes
    "2114705514911453262": "B05", "2113827833034219781": "B05", "2112602481587101759": "B05",
    "2114015538615906710": "B02", "2114062693367754888": "B02", "2114407527878107511": "B02",
    "2113613649457914197": "B04",   # Japan would thank America for the nuke
    "2113579061947605320": "B07",   # "Christians nuked Japan", answering the Muslims-are-radical post
    # Old grudges: the war-history posts
    "2112210311667216640": "B06", "2112744844485660990": "B06", "2112416156103655882": "B06",
    "2111990281470173464": "B06", "2114405724617077057": "B06",
    "2113310342738759850": "B12",   # a French politician called Japanese homes rabbit hutches
    "2112715090999066784": "B01",   # Westerners lectured Japan on anime diversity
    "2113982056552370332": "B18",   # Japan vs France or China vs Turkey, which is funnier?
    # Racial insults with no claim attached
    "2113968749518967138": "X02", "2114438258402771167": "X02",
}

# Per-post stance changes, where the default (owner camp supports, the other camp attacks, NEU neutral) is wrong.
STANCE = {
    # Japanese-speaking critics of the anime-purity reflex
    "2114634167267065862": "attacks", "2112782655821615269": "attacks", "2112472366987259925": "attacks",
    "2112441553100956089": "attacks", "2114634151399690296": "attacks", "2112418736137527412": "attacks",
    # The arrest data and its supporters
    "2113554141339668767": "attacks", "2112100272449245554": "attacks", "2111655764653900253": "attacks",
    "2114003881395159247": "attacks",
    "2112562881283928110": "attacks",  # the looted comic-store owner still supports the students
    # Japan's kindness: Japanese and neutral voices answering the French disappointment
    "2113953644013879574": "attacks", "2112398023473197212": "attacks", "2112171964181929994": "attacks",
    "2112159696316444942": "attacks", "2112163444711415880": "attacks", "2113663816357859695": "attacks",
    "2112333642106388483": "neutral",
    "2114777795452878911": "attacks",  # it is gross that the story becomes "the Japanese discriminated first"
    "2114274750537273799": "supports",  # mocking the Japanese is so easy it stops being funny
    "2114405724617077057": "attacks",  # Thai user: the French insult with the bomb's name, that crosses a line
}


def assign(uid, concept, side):
    b = BELIEF.get(uid) or FROM_CONCEPT[concept]
    own = OWNER[b]
    if uid in STANCE:
        s = STANCE[uid]
    elif own is None:
        s = "neutral"
    elif own == "ALL":
        s = "supports"
    elif side == own:
        s = "supports"
    elif side == "NEU":
        s = "neutral"
    else:
        s = "attacks"
    return b, s
