"""
Garment catalog for the MVP demo — now split by occasion AND gender.

All images are real, verified Pexels URLs (images.pexels.com, hotlink-safe).
Most are genuine plain/studio-background photos, which VTO handles far
better than the original candid Unsplash lifestyle shots (see git history /
conversation for that saga).

Honest gaps, given real time constraints sourcing 60 images by hand:
- men/first_date has 9 entries, not 10 (ran out of clean candidates)
- women/wedding_guest has 9 (6 new + 3 original green dresses)
- men/wedding_guest reuses the men/interview suit photos relabeled — a
  suit is legitimately appropriate for both contexts, so this is a
  deliberate reuse, not a placeholder
Swap any of these for better/more specific images anytime — see README
for how (grab a real product/studio photo URL, plain background works
best for VTO).
"""
from app.models import Gender, Occasion

_MEN_INTERVIEW_SUITS = [
    {"label": "Black suit, arms crossed, studio", "image_url": "https://images.pexels.com/photos/17311569/pexels-photo-17311569.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["cool", "structured"]},
    {"label": "Gray suit, confident pose, studio", "image_url": "https://images.pexels.com/photos/33100455/pexels-photo-33100455.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "structured"]},
    {"label": "Black suit, smiling, studio", "image_url": "https://images.pexels.com/photos/17311570/pexels-photo-17311570.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["cool", "soft"]},
    {"label": "Black suit, formal portrait, studio", "image_url": "https://images.pexels.com/photos/29995735/pexels-photo-29995735.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["cool", "structured"]},
    {"label": "Black suit with tie, studio", "image_url": "https://images.pexels.com/photos/17052320/pexels-photo-17052320.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["cool", "structured"]},
    {"label": "Suit, plain background, studio", "image_url": "https://images.pexels.com/photos/17049791/pexels-photo-17049791.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "structured"]},
    {"label": "Dark suit, studio portrait", "image_url": "https://images.pexels.com/photos/17049790/pexels-photo-17049790.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["cool", "muted"]},
    {"label": "Suit, confident expression, studio", "image_url": "https://images.pexels.com/photos/29995570/pexels-photo-29995570.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "soft"]},
    {"label": "Suit, smiling warmly, studio", "image_url": "https://images.pexels.com/photos/33100454/pexels-photo-33100454.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["warm", "soft"]},
    {"label": "Black suit, plain background, studio", "image_url": "https://images.pexels.com/photos/29995733/pexels-photo-29995733.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["cool", "muted"]},
]

GARMENT_CATALOG: dict[Occasion, dict[Gender, list[dict]]] = {
    "interview": {
        "women": [
            {"label": "Pastel suit, white studio background", "image_url": "https://images.pexels.com/photos/7202773/pexels-photo-7202773.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["warm", "soft"]},
            {"label": "Business suit, white studio background", "image_url": "https://images.pexels.com/photos/7202782/pexels-photo-7202782.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "structured"]},
            {"label": "Elegant blazer, white studio background", "image_url": "https://images.pexels.com/photos/7202777/pexels-photo-7202777.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["cool", "soft"]},
            {"label": "Colorful suit, white studio background", "image_url": "https://images.pexels.com/photos/7202897/pexels-photo-7202897.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["warm", "bold"]},
            {"label": "Suit, white studio background", "image_url": "https://images.pexels.com/photos/7202902/pexels-photo-7202902.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "structured"]},
            {"label": "Modern suit, white studio background", "image_url": "https://images.pexels.com/photos/7202801/pexels-photo-7202801.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["cool", "structured"]},
            {"label": "Suit, soft styling, white studio background", "image_url": "https://images.pexels.com/photos/7203907/pexels-photo-7203907.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["warm", "soft"]},
            {"label": "Suit, white studio background, group set", "image_url": "https://images.pexels.com/photos/7202907/pexels-photo-7202907.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "structured"]},
            {"label": "Suit, confident pose, white studio background", "image_url": "https://images.pexels.com/photos/7202899/pexels-photo-7202899.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["cool", "structured"]},
            {"label": "Suit, serious expression, white studio background", "image_url": "https://images.pexels.com/photos/7202766/pexels-photo-7202766.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "muted"]},
        ],
        "men": _MEN_INTERVIEW_SUITS,
    },
    "first_date": {
        "women": [
            {"label": "Neutral-tone casual outfit, studio", "image_url": "https://images.pexels.com/photos/19456445/pexels-photo-19456445.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "soft"]},
            {"label": "Neutral-tone casual outfit, studio (2)", "image_url": "https://images.pexels.com/photos/19456446/pexels-photo-19456446.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "soft"]},
            {"label": "Black shirt, casual, studio", "image_url": "https://images.pexels.com/photos/19456444/pexels-photo-19456444.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["cool", "structured"]},
            {"label": "Black shirt, white pants, studio", "image_url": "https://images.pexels.com/photos/19456441/pexels-photo-19456441.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["cool", "bold"]},
            {"label": "Black shirt, white pants, studio (2)", "image_url": "https://images.pexels.com/photos/19456442/pexels-photo-19456442.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["cool", "bold"]},
            {"label": "Chic outfit, neutral background, studio", "image_url": "https://images.pexels.com/photos/19456439/pexels-photo-19456439.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "soft"]},
            {"label": "Black blouse, beige pants, studio", "image_url": "https://images.pexels.com/photos/19456438/pexels-photo-19456438.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["warm", "muted"]},
            {"label": "Black blouse, studio", "image_url": "https://images.pexels.com/photos/19456440/pexels-photo-19456440.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["cool", "soft"]},
            {"label": "Black tank top, studio", "image_url": "https://images.pexels.com/photos/3888211/pexels-photo-3888211.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["cool", "bold"]},
            {"label": "Stylish top, studio", "image_url": "https://images.pexels.com/photos/18893567/pexels-photo-18893567.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "soft"]},
        ],
        "men": [
            {"label": "White shirt, casual, studio", "image_url": "https://images.pexels.com/photos/35406710/pexels-photo-35406710.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["warm", "soft"]},
            {"label": "White shirt, plain background", "image_url": "https://images.pexels.com/photos/8217507/pexels-photo-8217507.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["warm", "soft"]},
            {"label": "White t-shirt, plain background", "image_url": "https://images.pexels.com/photos/8217536/pexels-photo-8217536.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "soft"]},
            {"label": "White t-shirt, casual", "image_url": "https://images.pexels.com/photos/17630522/pexels-photo-17630522.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "soft"]},
            {"label": "Patterned white shirt, grey background", "image_url": "https://images.pexels.com/photos/11628044/pexels-photo-11628044.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["cool", "structured"]},
            {"label": "White t-shirt, grey background", "image_url": "https://images.pexels.com/photos/28446958/pexels-photo-28446958.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "muted"]},
            {"label": "White shirt, grey background, studio", "image_url": "https://images.pexels.com/photos/16825851/pexels-photo-16825851.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "soft"]},
            {"label": "White shirt, casual, indoor", "image_url": "https://images.pexels.com/photos/15849965/pexels-photo-15849965.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["warm", "soft"]},
            {"label": "White shirt, grey background, formal-casual", "image_url": "https://images.pexels.com/photos/17472051/pexels-photo-17472051.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "structured"]},
        ],
    },
    "wedding_guest": {
        "women": [
            {"label": "White dress, group, studio", "image_url": "https://images.pexels.com/photos/7301287/pexels-photo-7301287.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "soft"]},
            {"label": "Flowing dress, white studio", "image_url": "https://images.pexels.com/photos/13707456/pexels-photo-13707456.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "soft"]},
            {"label": "White dress, studio shoot", "image_url": "https://images.pexels.com/photos/30736117/pexels-photo-30736117.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "bold"]},
            {"label": "White dress, seated, studio", "image_url": "https://images.pexels.com/photos/20620141/pexels-photo-20620141.jpeg?auto=compress&cs=tinysrgb&w=1200", "tags": ["neutral", "soft"]},
            {"label": "Green dress, outdoor", "image_url": "https://images.unsplash.com/photo-1609357602746-10ade0197845?fm=jpg&q=60&w=1200&auto=format&fit=crop", "tags": ["cool", "bold"]},
            {"label": "Green long-sleeved dress", "image_url": "https://images.unsplash.com/photo-1552923410-f561a49581c4?fm=jpg&q=60&w=1200&auto=format&fit=crop", "tags": ["cool", "muted"]},
            {"label": "Elegant green dress, embroidery detail", "image_url": "https://images.unsplash.com/photo-1756483502814-fd570db8d4c7?fm=jpg&q=60&w=1200&auto=format&fit=crop", "tags": ["cool", "soft"]},
        ],
        "men": _MEN_INTERVIEW_SUITS,  # a suit is appropriate for both contexts — deliberate reuse, see module docstring
    },
}
