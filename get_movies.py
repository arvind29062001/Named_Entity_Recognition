import requests
from bs4 import BeautifulSoup
import json

# URL of the webpage containing the table
url = "https://www.sacnilk.com/entertainmenttopbar/Top_500_Bollywood_Movies_Of_All_Time"

# Send a GET request to the webpage
response = requests.get(url)

# Create a BeautifulSoup object to parse the HTML content
soup = BeautifulSoup(response.content, 'html.parser')

# Find the table element that contains the movie names
table = soup.find('table')

# Find all the rows in the table
rows = table.find_all('tr')

# Extract the movie names from each row
movie_names = []
for row in rows:
    # Assuming the movie name is in the first column (index 0) of each row
    columns = row.find_all('td')
    if columns:
        movie_name = columns[1].text.strip()
        movie_names.append(movie_name)

# Create a dictionary with the movie names
data = {"movies": movie_names}

# Save the movie list as JSON in a file
with open("movies.json", "w") as json_file:
    json.dump(data, json_file)

print("Movie list saved as movies.json.")