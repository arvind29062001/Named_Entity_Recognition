import spacy
from spacy.util import filter_spans
from spacy.tokens import Span
from spacy.language import Language
import re
import json

nlp = spacy.load("en_core_web_sm")

def filter_spans(spans):
    sorted_spans = sorted(spans, key=lambda span: (span.start, -span.end))
    result = []
    prev_start = -1
    prev_end = -1
    for span in sorted_spans:
        if span.start >= prev_start and span.end <= prev_end:
            continue  # Skip overlapping span
        result.append(span)
        prev_start = span.start
        prev_end = span.end
    return result

def generate_seat_patterns(rows, seats):
    patterns = []
    for row in range(1, rows + 1):
        for seat in range(1, seats + 1):
            patterns.append(f"Row {row}, Seat {seat}")
            patterns.append(f"{chr(64 + row)}{seat}")
            patterns.append(f"{chr(64 + row)}-{seat}")
            patterns.append(f"{chr(64 + row)}{chr(96 + seat)}")
            patterns.append(f"{chr(96 + seat)}{chr(64 + row)}")
            patterns.append(f"{chr(96 + seat)}-{chr(64 + row)}")
            patterns.append(f"{row}{seat}")
            patterns.append(f"{row}-{seat}")
            patterns.append(f"{row}{chr(96 + seat)}")
            patterns.append(f"{chr(96 + seat)}{row}")
            patterns.append(f"{chr(64 + row)}{seat + 1}")  # Append pattern like A12
    return patterns

@Language.component("find_seat_no")
def find_seat_no(doc):
    patterns = generate_seat_patterns(rows=10, seats=10)  # Update with the appropriate number of rows and seats
    seat_ents = []
    original_ents = list(doc.ents)

    seat_patterns = generate_seat_patterns(rows=10, seats=10)
    seat_regex = r"\b" + r"\b|\b".join(map(re.escape, seat_patterns)) + r"\b"

    seat_keywords = ["SEAT", "SEAT NO.", "SEAT:", "SEAT NO."]
    seat_keyword_regex = rf"(?:{'|'.join(seat_keywords)})[\s:]*([^\s:]+)"

    for match in re.finditer(seat_keyword_regex, doc.text, flags=re.IGNORECASE):
        start, end = match.span(1)
        span = doc.char_span(start, end)
        if span is not None:
            seat_ents.append((span.start, span.end, span.text))

    if not seat_ents:
        for match in re.finditer(seat_regex, doc.text):
            start, end = match.span()
            span = doc.char_span(start, end)
            if span is not None:
                seat_ents.append((span.start, span.end, span.text))
    
    # Special case for A12 pattern
    pattern = r"\b([A-Z]\d{2})\b"
    for match in re.finditer(pattern, doc.text):
        start, end = match.span(1)
        span = doc.char_span(start, end)
        if span is not None:
            seat_ents.append((span.start, span.end, span.text))

    for ent in seat_ents:
        start, end, name = ent
        per_ent = Span(doc, start, end, label="SEAT_NO")
        original_ents.append(per_ent)

    filtered = filter_spans(original_ents)
    doc.ents = filtered
    return doc



price_patterns = [
    r"(?<!\S)(rs\s?\d+(\.\d{2})?)",
    r"(?<!\S)(\d+(\.\d{2})?\s?rs)",
    r"(?<!\S)(\d+(\.\d{2})?\s?usd)",
    r"(?<!\S)(usd\s?\d+(\.\d{2})?)",
    r"(?<!\S)(\d+(\.\d{2})?\s?usd)",
    r"(?<!\S)(rs\.\s?\d+(\.\d{2})?)",  # Matches patterns like Rs.178.32
    r"(?<!\S)(\d+(\.\d{2})?\s?rs\.)",  # Matches patterns like 178.32 Rs.
]

@spacy.Language.component("find_price")
def find_price(doc):
    text = doc.text.lower()  # Lowercase the input text
    price_ents = []
    original_ents = list(doc.ents)
    for pattern in price_patterns:
        for match in re.finditer(pattern, text):
            start, end = match.span()
            span = doc.char_span(start, end)
            if span is not None:
                price_ents.append((span.start, span.end, span.text))
    for ent in price_ents:
        start, end, name = ent
        price_ent = Span(doc, start, end, label="PRICE")
        original_ents.append(price_ent)
    filtered = filter_spans(original_ents)
    doc.ents = filtered
    return doc



date_patterns = [
    r"\b\d{1,2}(?:st|nd|rd|th)?\s(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s\d{2,4}\b",  # Matches formats like dd Month yyyy
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s\d{1,2}(?:st|nd|rd|th)?(?:,)?\s\d{2,4}\b",  # Matches formats like Month dd yyyy
    r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b",  # Matches formats like dd/mm/yyyy, dd-mm-yyyy, dd.mm.yyyy
    r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2}\b",  # Matches formats like dd/mm/yy, dd-mm-yy, dd.mm.yy
    r"\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b",  # Matches formats like yyyy/mm/dd, yyyy-mm-dd, yyyy.mm.dd
    r"\b\d{2}[./-]\d{1,2}[./-]\d{1,2}\b",  # Matches formats like yy/mm/dd, yy-mm-dd, yy.mm.dd
    r"\b\d{1,2}[./-]\d{4}[./-]\d{1,2}\b",  # Matches formats like dd/yyyy/mm, dd-yyyy-mm, dd.yyyy.mm
    r"\b\d{1,2}[./-]\d{2}[./-]\d{1,2}\b",  # Matches formats like dd/yy/mm, dd-yy-mm, dd.yy.mm
    r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun), \d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec), \d{4}",
    r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun), \d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b"  # Matches format like Thu, 23 Mar
]



@spacy.Language.component("find_date")
def find_date(doc):
    text = doc.text
    date_ents = []
    original_ents = list(doc.ents)

    # Find dates using patterns
    for pattern in date_patterns:
        for match in re.finditer(pattern, doc.text):
            start, end = match.span()
            span = doc.char_span(start, end)
            if span is not None:
                date_ents.append((span.start, span.end, span.text))
    
    # Find dates preceded by "DATE", "Date", "DATE:", or "Date:"
    date_prefixes = ["DATE", "Date", "DATE:", "Date:"]
    for prefix in date_prefixes:
        pattern = r"\b" + re.escape(prefix) + r"\s*([\w.-]+)"
        for match in re.finditer(pattern, doc.text):
            start, end = match.span(1)
            span = doc.char_span(start, end)
            if span is not None:
                date_ents.append((span.start, span.end, span.text))

    # Add identified date entities to the original entities
    for ent in date_ents:
        start, end, name = ent
        per_ent = Span(doc, start, end, label="DATE")
        original_ents.append(per_ent)

    # Filter and update the entities
    filtered = filter_spans(original_ents)
    doc.ents = filtered
    return doc


time_patterns = [
    r"\b\d{1,2}:\d{2}\s?(?:AM|PM|am|pm)\b",  # Matches patterns like 4:00 PM, 10:30 am, etc.
    r"\b\d{1,2}:\d{2}\s?(?:A\.M\.|P\.M\.|a\.m\.|p\.m\.)\b",  # Matches patterns like 4:00 P.M., 10:30 a.m., etc.
    # Add more patterns as needed
]

@spacy.Language.component("find_time")
def find_time(doc):
    text = doc.text
    time_ents = []
    original_ents = list(doc.ents)
    for pattern in time_patterns:
        for match in re.finditer(pattern, doc.text):
            start, end = match.span()
            span = doc.char_span(start, end)
            if span is not None:
                time_ents.append((span.start, span.end, span.text))
    for ent in time_ents:
        start, end, name = ent
        per_ent = Span(doc, start, end, label="TIME")
        original_ents.append(per_ent)
    filtered = filter_spans(original_ents)
    doc.ents = filtered
    return doc


# ticket_pattern = r"(?i)\b(?:TICKET NO\.?|BOOKING NO\.?|BOOKING ID\.?|TICKET ID\.?)\s*:\s*\b([A-Za-z\d]+)\b|\b([A-Za-z\d]{8})\b"
ticket_pattern = r"(?i)(?:booking id|ticket no)\s*[ :-]*\b([A-Za-z\d]+)\b|\b([A-Za-z\d]{8})\b"


@spacy.Language.component("find_ticket_no")
def find_ticket_no(doc):
    ticket_ents = []
    original_ents = list(doc.ents)
    lowercase_text = doc.text.lower()
    for match in re.finditer(ticket_pattern, lowercase_text):
        start, end = match.span(1)
        span = doc.char_span(start, end)
        if span is not None:
            ticket_ents.append((span.start, span.end, span.text))
    for ent in ticket_ents:
        start, end, name = ent
        per_ent = Span(doc, start, end, label="TICKET_NO")
        original_ents.append(per_ent)
    filtered = filter_spans(original_ents)
    doc.ents = filtered
    return doc


def ignore_brackets(text):
    result = ""
    bracket_count = 0

    for char in text:
        if char == '(':
            bracket_count += 1
        elif char == ')':
            bracket_count -= 1
        elif bracket_count == 0:
            if char == '\n':
                result += ' '  # Join newline with a space
            else:
                result += char

    return result



# Load the movie names from the JSON file
with open("movies.json", "r") as f:
    movie_names = [name.lower() for name in json.load(f)]

@Language.component("find_movie_name")
def find_movie_name(doc):
    movie_ents = []
    original_ents = list(doc.ents)

    # Check if the extracted text forms a movie name
    for token in doc:
        extracted_text = token.text
        extracted_text = ignore_brackets(extracted_text)
        
        # print(extracted_text)
        tokens = extracted_text.split()
        for i in range(len(tokens)):
            for j in range(i + 1, len(tokens) + 1):
                partial_name = " ".join(tokens[i:j])
                lowercase_partial_name = partial_name.lower()
                for movie_name in movie_names:
                    lowercase_movie_name = movie_name.lower()
                    if lowercase_partial_name == lowercase_movie_name:
                        movie_ent = Span(doc, token.i + i, token.i + j, label="MOVIE")
                        movie_ents.append(movie_ent)

    # Add identified movie name entities to the original entities
    original_ents.extend(movie_ents)

    filtered = filter_spans(original_ents)
    doc.ents = filtered
    return doc






nlp.add_pipe("find_seat_no", before="ner")
nlp.add_pipe("find_date", before="ner")
nlp.add_pipe("find_price", before="find_seat_no")
nlp.add_pipe("find_time", before="ner")
nlp.add_pipe("find_ticket_no", before="ner")
nlp.add_pipe("find_movie_name",before="ner")


test = '''
KABZAA
ONO
Your Ticket
Tap for support, details & more actions
Kabzaa (U/A)
Kannada, 2D
Thu, 23 Mar | 11:15 AM
Sri Radhakrishna Theatre, 4K Dolby Atmos: RT Nagar
Total Amount
1 Ticket(s)
RADHAKRISHNA
SILVER-A12
BOOKING ID: W28HJJV
Cancellation unavailable : cut-off time of 4 hrs
before showtime has passed
2 FREE* movie tickets,
waiting just for you!
Apply Now
b
M-Ticket
Rs.178.32
play
By beckshow Siddhant Manchandani
X
*T & C Apply
'''

doc = nlp(test)

# Print the modified named entities after applying the custom components
for ent in doc.ents:
    if ent.label_ == "DATE":
        print(ent.text, ": DATE")
    elif ent.label_=="MOVIE" or ent.label_=="WORK_OF_ART":
        print(ent.text,": MOVIE")
    elif ent.label_ == "TIME":
        print(ent.text, ": TIME")
    elif ent.label_ == "SEAT_NO":
        print(ent.text, ": SEAT NO")
    elif ent.label_=="TICKET_NO":
        print(ent.text," : TICKET NO.")
    elif ent.label_ == "PRICE"or ent.label_=="MONEY":
        print(ent.text, ": PRICE")
    elif ent.label_=="GPE":
        print(ent.text,": VENUE")

