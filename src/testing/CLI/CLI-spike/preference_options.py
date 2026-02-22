"""
Docstring for preference_options

Stores all the categorical and numerical range preference options for each preference
"""

# "genres": [],
# "release_range": (),
# "number_of_players": None,
# "length": None,

GENRE_OPTIONS = ['Action',
 'Adventure',
 'Casual',
 'Early-Access',
 'Free-to-Play',
 'Game-Development',
 'Gore',
 'Indie',
 'Massively-Multiplayer',
 'Movie',
 'Nudity',
 'RPG',
 'Racing',
 'Sexual-Content',
 'Simulation',
 'Sports',
 'Strategy',
 'Violent',
]

def get_options(preference: str):
    match (preference):
        case "genre":
            return GENRE_OPTIONS
        case _:
            raise ValueError(f"Recieved invalid preference value: {preference}")
    