import json
def convert_to_single_line(text):
    # Replace newline characters with a space
    single_line_text = text.replace('\n', ' ')
    
    # Remove any leading or trailing whitespace
    single_line_text = single_line_text.strip()
    
    return single_line_text

def generate_substrings(text):
    substrings = []
    words = text.split()
    n = len(words)
    for i in range(n):
        for j in range(i+1, n+1):
            substring = ' '.join(words[i:j])
            substrings.append(substring)
    return substrings

def find_movie_substrings(text):
    substrings = generate_substrings(text)
    
    with open("movies.json", "r") as file:
        movies = json.load(file)
    
    for substring in substrings:
        if substring.lower() in [movie.lower() for movie in movies]:
            print(substring)

text = '''KABZAA
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
'''
text=convert_to_single_line(text)
find_movie_substrings(text)









