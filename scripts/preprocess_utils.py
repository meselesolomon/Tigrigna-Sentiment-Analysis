
# import libraries
import re


# Tigrigna stop words
TIGRIGNA_STOPWORDS = [
    'ሞ', 'ቲ', 'ታ', 'ኳ', 'ውን', 'ዚ', 'የ', 'ዩ', 'ያ', 'ዮም', 'ዮን',
    'እሞ', 'እቲ', 'እታ', 'እኳ', 'እዚ', 'እየ', 'እዩ', 'እያ', 'እዮም', 'እዮን',
     'ሕጂ', 'መበል', 'መን', 'መንጎ', 'ምስ',
    'ምባል', 'ምእንቲ', 'ስለ', 'ስለዚ','ስለዝበላ', 'ሽዑ', 'በለ', 'በቲ', 'በዚ', 'ብምባል',
    'ነዚ', 'ናብ', 'ናብቲ', 'ናትኩም', 'ናትኪ', 'ናትካ', 'ናትክን',
    'ናይ', 'ናይቲ', 'ንሕና', 'ንሱ', 'ንሳ', 'ንሳቶም', 'ንስኺ', 'ንስኻ', 'ንስኻትኩም', 'ስኻትክን',
    'ንዓይ', 'ኢና', 'ኢኻ', 'ኢዩ', 'ኣብ', 'ኣብቲ', 'ኣብታ', 'ኣብኡ', 'ኣብዚ', 'ኣነ', 'እተን', 'እቶም',
    'እንከሎ', 'እዋን', 'እዛ', 'እዞም', 'እየን',  'ከም', 'ከምቲ',
    'ከምዘሎ', 'ከምዚ', 'ከኣ', 'ኩሉ', 'ካልእ', 'ካልኦት', 'ካብ', 'ካብቲ', 'ካብቶም',
    'ክብል', 'ክንዲ', 'ኸም', 'ኸኣ','ወይ','ን', 'ብ', 'ድማ', 'ገለ', 'አንታ'
]

# Tigrigna character normalization map
NORMALIZATION_MAP = {
    'ጸ':'ፀ','ጹ':'ፁ','ጺ':'ፂ','ጻ':'ፃ','ጼ':'ፄ','ጽ':'ፅ','ጾ':'ፆ',
    'ሠ':'ሰ','ሡ':'ሱ','ሢ':'ሲ','ሣ':'ሳ','ሤ':'ሴ','ሥ':'ስ','ሦ':'ሶ',
    'ኀ':'ሀ','ኁ':'ሁ','ኂ':'ሂ', 'ኃ':'ሃ','ኄ':'ሄ','ኅ':'ህ','ኆ':'ሆ'
}

# Tigrigna abbreviations and their expansions 
TIGRIGNA_ABBREVIATIONS = {
    r'መ\s?/\s?ር': 'መምህር', r'ፕ\s?/\s?ት': 'ፕሬዚደንት', r'ዶ\s?/\s?ር': 'ዶክተር',
    r'ጠ\s?/\s?ሚ': 'ጠቅላይ ሚኒስተር', r'ወ\s?/\s?ሮ': 'ወይዘሮ', r'ጀ\s?/\s?ል': 'ጀነራል',
    r'ት\s?/\s?ም': 'ትምህርት ሚኒስቴር', r'ሚ\s?/\s?ኒ': 'ሚኒስቴር', r'ቤ\s?/\s?ጽ': 'ቤት ጽሕፈት',
    r'ቤ\s?/\s?ፍ\s?/\s?ዲ': 'ቤት ፍርዲ', r'ዓ\s?/\s?ም': 'ዓመተ ምህረት', r'ኢ\s?/\s?ያ': 'ኢትዮጵያ',
    r'ገ\s?/\s?ማርያም': 'ገብረ ማርያም', r'ሃ\s?/\s?ስላሴ': 'ሃይለ ስላሴ', r'እ\s?/\s?ር': 'እግዚአብሄር',
    r'ክ\s?/\s?ዘመን': 'ክፍለ ዘመን', r'ም\s?/\s?ያቱ': 'ምክንያቱ'
}

# Emoji pattern to remove emojis from text
EMOJI_PATTERN = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+", flags=re.UNICODE)
trans_table = str.maketrans(NORMALIZATION_MAP)

# Preprocessing function that incorporates all the cleaning steps 
def expand_abbreviations(text):
    for abbr_pattern, full_form in TIGRIGNA_ABBREVIATIONS.items():
        text = re.sub(abbr_pattern, full_form, text)
    return text

# This function is the heart of our preprocessing pipeline
def clean_tigrigna_text(text):
    if not isinstance(text, str) or text == "":
        return ""

    # A. Reductions (Added our discussed repeated character logic)
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)

    # B. Expansion & Web noise
    text = expand_abbreviations(text)
    text = re.sub(r"<.*?>", " ", text)
    text = re.sub(r"http\S+|www\S+|https\S+", " ", text)

    # C. Character Normalization
    text = text.translate(trans_table)

    # D. Handle Emojis
    text = EMOJI_PATTERN.sub(r"", text)

    # E. Remove Ge'ez Punctuation, Numbers, and Latin noise
    text = re.sub(r"[፡።፣፤፥፦፧፨፠፩-፼]", " ", text)
    text = re.sub(r"[.,!?;:\"'(){}\[\]\-]", " ", text)
    text = re.sub(r"\d+", " ", text)

    # F. Safety Net: Keep only Ge'ez script and spaces
    text = re.sub(r"[^\u1200-\u137F\s]", " ", text)

    # G. Stopword removal & Space normalization
    text = re.sub(r'\s+', ' ', text).strip()
    words = text.split()
    words = [w for w in words if w not in TIGRIGNA_STOPWORDS]

    return " ".join(words) # Returns a string for Deep Learning models
    
