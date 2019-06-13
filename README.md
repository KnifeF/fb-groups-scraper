# Scrape FB Groups data with Python
1) Using Python and various tools to scrape/parse/store facebook data that is related 
to fb groups (group details, group's posts, searching keywords in posts, map groups 
that a profile is a member of them, etc.)
2) The scripts get facebook profiles (User IDs) OR Keywords & groupIDs as an input 
(through Tkinter GUI), navigates to related facebook web pages and groups' data for scraping, 
and then - generates reports as an output (of fb groups data). 
3) The process is based on tools like Selenium WebDriver, BeautifulSoup, 
and re - to automate the scraping process, trying to simulate a human behaviour, 
and parse some HTML. 
4) The output data is stored in various ways (as csv, txt, or as Nodes & Relationships 
in Neo4J Graph Database), and the scripts are using tools like Py2neo and Pandas 
to organize the unstructured data.
5) This might be a useful way to organize an unstructured social web data (including: 
profiles' groups, groups' posts, etc.) within a Graph database that can 
describe social connections with Cypher queries, or store the data to local files, 
for various purposes (including OSINT/DeepWeb/WEBINT/Competitive intelligence).

## Some notes:
1) This is an old, basic and messy code (or version) that I have written for 
educational purposes. It requires a registered profile (logged-in to FB before 
the program starts) in order to view the required content for the scraping process.
2) The program is not using an official API (the data is parsed from HTML tags, 
regular expression operations, etc.). According to frequent changes in these websites 
on their client-side development, the data might not be extracted/parsed as expected 
(the structure of the html is changed often, and a long time passed since I have 
actually written the code), so when I find time for it, I will possibly update the 
code and write a "cleaner" one with more features.
3) You are also welcome to offer updates to the code and other ideas (if you understand 
something through all this mess).

## Disclaimer:
The scripts / tools are for educational purposes only, 
and they might violate some websites (including social media) TOS. 
Use at your own risk.
