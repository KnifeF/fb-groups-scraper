"""The program gets fb profile targets (uids) as an input (through Tkinter GUI),
to scrape their groups' data, and then generates csv reports, or stores the data
to Neo4J GDB (using 'py2neo' library). The process is based on tools like
selenium webdriver, beautifulsoup, re - to scrape the web & parse some html.

This is an old, basic and messy code that I have written for educational purposes.
*You may see more details on the README.md file.

## Disclaimer:
The scripts / tools are for educational purposes only,
and they might violate some websites (including social media) TOS.
Use at your own risk."""
import codecs
import glob
import pandas as pd
from tkinter.filedialog import *
from tkinter.scrolledtext import *
from selenium import webdriver
from selenium.common.exceptions import *
from bs4 import BeautifulSoup
from py2neo import Graph, Node, Relationship
from datetime import *
from time import sleep
from random import randint
from neo4j_on_webdriver import run_neo_server

__author__ = "KnifeF"
__license__ = "MIT"
__email__ = "knifef@protonmail.com"

# ****************************************WebDriver Settings / other parameters*********************************
WITHOUT_EXTENSIONS = "--disable-extensions"  # disable extensions
# Use Cookies
ARGUMENTS = r'user-data-dir='+os.path.join(os.environ["HOMEPATH"],
                                           r'AppData\Local\Google\Chrome\User Data')
# path to 'chromedriver'
CHROME_DRIVER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chromedriver')
# Disable JavaScript From Browser
JS_PREFERENCE = {'profile.managed_default_content_settings.javascript': 2}
PREFERENCES_PATH = os.path.join(os.environ["HOMEPATH"],
                                r'AppData\Local\Google\Chrome\User Data\Default')
# path to store csv files
SAVE_PATH = os.path.join(os.environ["HOMEPATH"], "DESKTOP", "CSV", "groups")
# columns of output csv files
GROUP_COLUMNS = [r"UID", r"Profile Name", r"Group Name", r"Group ID",
                 r"Members", r"Group Type", r"Time Stamp"]
FB_URL = "https://www.facebook.com"  # basic fb url
# basic fb url for mobile when js is disabled
FB_URL2 = "https://mbasic.facebook.com"
# query for fb profile's groups by his uid
GROUPS_URL = FB_URL+"/search/[FID]/groups"
# xpath for a link/button that contains 'Groups' as text
GROUPS_BTN = r"//a[text()[contains(.,'Groups')]]"
# xpath for a link/button that contains 'Home' as text
HOME_BTN = r"//a[text()[contains(.,'Home')]]"
# xpath for a link/button that contains 'About' as text
ABOUT_BTN = r"//a[text()[contains(.,'About')]]"
NEO_PASSWORD = "my_password"  # password to access neo4j db server


# ****************************************GUI Functions****************************************************
class GuiMenu(Tk):
    """
    Tk GUI object as 'GuiMenu' for launching the 'GroupsScraper'
    """
    def __init__(self):
        """
        Builds a Tk GUI object ('GuiMenu') with required parameters
        """
        super().__init__()
        self.title("Groups Scraper")
        self.resizable(0, 0)
        # self.iconbitmap(r'Facebook.ico')
        self.config(background="black")
        self.profiles_lst = []
        self.is_unknown_groups_q = False
        self.is_visualize_neo = False
        # *******************************Menu****************************************
        menu = Menu(self)
        file_menu = Menu(menu)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open...", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Clear Text", command=self.clear_text)
        file_menu.add_command(label="Check Groups Privacy!",
                              command=self.check_group_privacy_q)
        file_menu.add_command(label="Visualize Groups!",
                              command=self.visualize_with_neo)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        help_menu = Menu(menu)
        menu.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About...", command=self.about)
        self.config(menu=menu)
        # *******************************Labels**************************************
        Label(self, text="Groups Scraper", background='black',
              foreground='red', font=("Lucida Grande", 20, 'bold')).pack()
        Label(self, text="Please Enter A List Of Facebook Users' IDS:",
              background='black', foreground='white',
              font=("Lucida Grande", 10, 'italic')).pack()
        # *******************************Scrolled Text*******************************
        self.text = ScrolledText(self, background='black', foreground='red',
                                 insertbackground="red", font=("Lucida Grande", 10),
                                 width=40, height=5)
        self.text.pack()
        # *******************************Labels**************************************
        Label(self, text="*Note: you have to be logged in to facebook "
                         "before scraping groups.", background='black',
              foreground='red', font=("Lucida Grande", 8)).pack()
        # *******************************Buttons*************************************
        Button(self, text='Quit', background="black", foreground="white",
               font=("Lucida Grande", 12, 'bold'), command=self.destroy)\
            .pack(side=RIGHT)
        Button(self, text='Scrape Groups!', background="black",
               foreground="white", font=("Lucida Grande", 12, 'bold'),
               command=self.scrape_entered_users_groups).pack(side=RIGHT)

        mainloop()  # Run the main loop of Tcl. (tk mainloop)

    def scrape_entered_users_groups(self):
        """
        Creates list with entered profiles (ScrolledText),
        and exits GUI window
        :return:
        """
        if self.text:
            profiles = (self.text.get(0.0, END)).split("\n")
            for row in profiles:
                stripped_profile = row.strip()
                ok = (stripped_profile is not "") and (stripped_profile is not " ") and \
                     (stripped_profile.isdigit())
                if ok:
                    self.profiles_lst.append(stripped_profile)
            if self.profiles_lst or ('check_groups=unknown_privacy' in profiles) \
                    or ('visualize_with_neo4j' in profiles):
                if 'check_groups=unknown_privacy' in profiles:
                    self.is_unknown_groups_q = True
                if 'visualize_with_neo4j' in profiles:
                    self.is_visualize_neo = True
                self.destroy()

    def clear_text(self):
        """
        Clears all written text in Tk GUI (ScrolledText)
        :return:
        """
        if self.text:
            self.text.delete(0.0, END)

    def open_file(self):
        """
        Upload a .txt file to Tk GUI (ScrolledText)
        :return:
        """
        try:
            f = askopenfile(title="Select file",
                            filetypes=(("text files", "*.txt"), ))
            t = f.read()
            self.text.delete(0.0, END)
            self.text.insert(0.0, t)
        except AttributeError:
            pass

    def check_group_privacy_q(self):
        """
        Inserts 'Check_Groups=Unknown_privacy' query to
        Tk GUI (ScrolledText)
        :return:
        """
        try:
            self.text.delete(0.0, END)
            self.text.insert(0.0, 'check_groups=unknown_privacy')
        except AttributeError:
            pass

    def visualize_with_neo(self):
        """
        option to add output data from FB to Neo4J Graph DB
        :return:
        """
        try:
            self.text.delete(0.0, END)
            self.text.insert(0.0, 'visualize_with_neo4j')
        except AttributeError:
            pass

    def save_file(self):
        """
        Saves profiles' list (from ScrolledText) to a text file
        :return:
        """
        try:
            # Ask for a filename to save as, and returned the opened file
            f = asksaveasfile(mode='w', filetypes=(("text files", "*.txt"), ))
            if f is None:
                return
            profiles = (self.text.get(0.0, END)).split("\n")
            for row in range(len(profiles)):
                stripped_profile = profiles[row].strip()
                ok = (stripped_profile is not "") and (stripped_profile is not " ") and \
                     (stripped_profile.isdigit())
                if ok:
                    f.write(stripped_profile+"\n")
            f.close()
        except AttributeError:
            pass

    def about(self):
        """
        Display the instructions in Tk GUI (ScrolledText)
        :return:
        """
        if self.text:
            instructions_str = "Enter a list* of profiles to crawl, or open a text \n" \
                               "file with a list of profiles.\n" + \
                               "Then, click on the button --> 'Scrape Groups!'\n" + \
                               "to start the collection from facebook.\n\n" \
                               "* Hit 'Enter' between each user, e.g:\n\n" + \
                               "100001234567\n"+"10000054321"
            self.text.delete(0.0, END)
            self.text.insert(0.0, instructions_str)


# ****************************************Groups Scraper Functions*******************************************
class GroupsScraper:
    """
    GroupsScraper handles the scraping process of profiles' groups data
    (scraping fb profile content that is related to his fb groups)
    """
    def __init__(self, fb_target_ids, js_enabled):
        """
        Builds object that handles groups' scraping process
        (of facebook targets)
        :param fb_target_ids: target ids to Crawl (list)
        :param js_enabled: is javascript required as enabled (boolean)
        """
        self.fb_target_ids = fb_target_ids
        self.js_enabled = js_enabled
        self.p_sources_list = []
        # Set chromedriver to the desirable mode (adds arguments to ChromeOptions)
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(WITHOUT_EXTENSIONS)
        chrome_options.add_argument(ARGUMENTS)
        if not js_enabled:
            # Adds an experimental option which is passed to chrome to disable js
            chrome_options.add_experimental_option("prefs", JS_PREFERENCE)
        self.driver = None
        try:
            # Creates a new instance of the chrome driver
            self.driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH,
                                           chrome_options=chrome_options)
            self.driver.maximize_window()
        except WebDriverException:
            print("Failed to start driver at: " + CHROME_DRIVER_PATH)
            exit()
        create_dir(SAVE_PATH)

    def crawl_groups(self):
        """
        Navigates to the required URLs, crawls FB pages and append
        sources to a list
        :return:
        """
        if self.driver and self.fb_target_ids:
            # Loads a web page in the current browser session (GET url)
            self.driver.get(FB_URL)
            sleep(randint(2, 4))
            # Checks if the program user is logged in to fb
            if self.is_logged_in():
                for target_id in self.fb_target_ids:
                    # url with query to profile page
                    profile_url = FB_URL+"/"+"profile.php?id="+target_id
                    # url with query to groups of a profile page
                    profile_groups_url = GROUPS_URL.replace("[FID]", target_id)
                    print("target urls\n***************\n" + profile_url + "\n"
                          + profile_groups_url + "\n\n")
                    public_groups_source = None

                    # Crawling profile's public groups (depends on profile's
                    # privacy settings - Group Section)
                    sleep(randint(6, 16))
                    # Navigates to profile's timeline
                    self.driver.get(profile_url)
                    sleep(randint(3, 6))
                    # Navigates to profile's public groups
                    ok = self.navigate_to_public_groups()
                    if ok:
                        print("Profile found!")
                        if ("groups" in self.driver.current_url) and \
                                ("Public" in self.driver.page_source):
                            print("profile's public groups found")
                            # Gets the source of the current page.
                            public_groups_source = self.driver.page_source
                            print("Finished crawling --> " + profile_url)

                        # Crawling profile's all groups (including closed groups)
                        sleep(randint(5, 10))
                        # get url with query to groups of a profile page
                        self.driver.get(profile_groups_url)
                        # scrolling page to get more data from page
                        self.scroll_down_page()
                        # Gets the source of the current page.
                        all_groups_source = self.driver.page_source
                        if "Sorry, we couldn't understand this search" \
                                not in all_groups_source:

                            print("profile's groups found")
                            self.p_sources_list.append((target_id, all_groups_source,
                                                        public_groups_source))
                            print("Finished crawling --> " + profile_groups_url)

                        # Decides randomly to navigates home
                        to_home = randint(1, 4)
                        sleep(randint(3, 15))
                        if to_home == 3:
                            self.navigate_home()
                    else:
                        print("Profile Not found!")
                sleep(2)
                # navigates home
                self.navigate_home()
            sleep(randint(2, 5))
            # Closes the current window of the WebDriver.
            self.driver.close()

    def navigate_home(self):
        """
        navigates from the current facebook page to
        facebook's home page (main page)
        :return:
        """
        try:
            if self.driver.find_elements_by_xpath(HOME_BTN):
                # Clicks 'Home' button
                self.driver.find_elements_by_xpath(HOME_BTN)[0].click()
            sleep(randint(2, 4))
        except ElementNotVisibleException:
            print("ElementNotVisibleException")
            pass
        except WebDriverException:
            print("WebDriverException")
            pass

    def navigate_to_public_groups(self):
        """
        navigates from profile's timeline to his public groups
        :return: boolean - True if succeed to navigate to profile's
        public groups, or False.
        """
        ok = False
        try:
            current_source = self.driver.page_source
            if ("This Page Isn't available" in current_source) or \
                    ("page may have been removed" in current_source) or \
                    ("The link" in current_source and "broken" in current_source):
                return False

            if ("Timeline" in current_source) and \
                    self.driver.find_elements_by_xpath(ABOUT_BTN):
                ok = True
                self.driver.find_elements_by_xpath(ABOUT_BTN)[0].click()
                sleep(randint(2, 3))
                self.scroll_down_page()  # scrolling the page
                # Depends on profile's privacy
                if self.driver.find_elements_by_xpath(GROUPS_BTN):
                    sleep(randint(1, 4))
                    # Clicks 'Groups' button
                    self.driver.find_elements_by_xpath(GROUPS_BTN)[0].click()
                    sleep(randint(2, 3))
                    self.scroll_down_page()  # scrolling the page
        except ElementNotVisibleException:
            print("ElementNotVisibleException")
            pass
        except WebDriverException:
            print("WebDriverException")
            pass
        return ok

    def is_logged_in(self):
        """
        Checks if the program user is logged in to facebook
        :return: Boolean - True if the user is logged-in, or False.
        """
        sleep(3)
        try:
            # Gets the source of the current page.
            current_source = self.driver.page_source
            if current_source:
                # BeautifulSoup obj to parse some HTML
                soup = BeautifulSoup(current_source, 'html.parser')
                page_title = soup.title.string  # web page title
                if not("Log In" in page_title or "Sign Up" in page_title):
                    return True
        except WebDriverException:
            print("WebDriverException")
            pass
        return False

    def scroll_down_page(self):
        """
        Handles crawling process and scrolling page to get more
        data from target url (javascript enabled)
        :return:
        """
        sleep(randint(3, 6))
        # Get WebDriver current URL
        tmp_url = self.driver.current_url
        sleep(2)
        # Get scroll height
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        count = 0
        while True:
            # Scroll down page to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # Wait to load page (delay)
            sleep(randint(1, 3))
            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            sleep(randint(1, 3))
            if new_height == last_height:
                count += 1
                if 'about' in tmp_url:
                    # Indicates navigation in profile's 'About' page and
                    # searches for 'Public Groups'. Scrolls down till the string
                    # is found on WebDriver page_source
                    if ("Public" in self.driver.page_source) and \
                            ("Groups" in self.driver.page_source):
                        sleep(randint(1, 2))
                        break

                elif (count >= 5) or ("End of Results" in self.driver.page_source) or \
                        ("We couldn't find anything for" in self.driver.page_source) \
                        or ("Bing Privacy Policy" in self.driver.page_source):
                    # scrolls down till the string that indicates 'End of Results' is found
                    # on WebDriver page_source
                    sleep(randint(1, 2))
                    break
            else:
                count = 0
            last_height = new_height

    def groups_privacy_deep_search(self):
        """
        Traversing all csv files from dir (contain facebook's groups data),
        trying to find all groups with 'Unknown' privacy status.
        Then, Crawling these facebook groups' URLs, parses their privacy,
        and saves changes to csv (group's privacy should be 'Public Group'
        or 'Closed Group').
        :return:
        """
        if (not self.js_enabled) and os.path.isdir(SAVE_PATH):
            # Sort csv files from given path (directory), by their size
            csv_files = sort_files_by_size(glob.glob1(SAVE_PATH, "*.csv"), SAVE_PATH)
            if csv_files:
                # Navigates to facebook url (in a mobile version - without JavaScript)
                self.driver.get(FB_URL2)
                sleep(randint(2, 4))
                # Checks if the program user is logged in to fb
                if self.is_logged_in():
                    file_counter = 0
                    for f_name in csv_files:
                        # opens csv file with pandas
                        df = pd.read_csv(os.path.join(SAVE_PATH, f_name))
                        # finds csv file that has group with 'Unknown' privacy
                        # (probably because privacy concerns - a user may set public
                        # groups as not visible on 'about' section)
                        if (not df.empty) and ("Unknown" in df[r"Group Type"][0]):
                            # creates list from 'Group ID' column of 'df'
                            target_urls = list(df[r"Group ID"])
                            # creates list from 'Group Type' column of 'df'
                            group_types = list(df[r"Group Type"])
                            count_url_change = 0
                            old_group_title = ""

                            if file_counter > 0 and len(target_urls) > 40:
                                # sleep between url GET requests after scraping some
                                # targets data
                                sleep(randint(20, 4*60))
                            else:
                                sleep(randint(5, 90))
                            file_counter += 1

                            for i in range(len(target_urls)):
                                # check if a group privacy is unknown (within
                                # 'Group Type' column)
                                if "Unknown" in group_types[i]:
                                    # converts target fb url to a mobile version url
                                    tmp_url = target_urls[i].replace(FB_URL, FB_URL2)
                                    if (FB_URL2 in tmp_url) and ('/groups/' in tmp_url):
                                        # Navigates to facebook group URL (mobile version)
                                        self.driver.get(tmp_url)
                                        sleep(randint(2, 3))
                                        # WebDriver pages source
                                        current_source = self.driver.page_source
                                        # Indicates navigation to group (if 'Join Group' appears)
                                        if current_source and ("Join Group" in current_source):
                                            # BeautifulSoup obj to parse some HTML
                                            soup = BeautifulSoup(current_source, 'html.parser')
                                            # Gets facebook page's title (name of the group)
                                            new_group_title = soup.title.string
                                            # Checks if the title was changed
                                            if new_group_title != old_group_title:
                                                # Indicates that the group is 'public'
                                                if "Public Group" in current_source:
                                                    group_types[i] = "Public Group"
                                                # Indicates that the group is 'closed'
                                                elif "Closed Group" in current_source:
                                                    group_types[i] = "Closed Group"
                                            old_group_title = new_group_title

                                        # Handles random delays for scraper after
                                        # viewing 10-25 groups (act more randomly and slow
                                        # like a human, to not abuse with many requests in
                                        # a short amount of time)
                                        if count_url_change > randint(10, 25):
                                            # more delay
                                            count_url_change = 0
                                            sleep(randint(10, 100))
                                        else:
                                            # less delay
                                            sleep(randint(5, 20))

                                        # Handles random navigation to home page
                                        # (act more like human)
                                        if randint(0, 8) == 4:
                                            self.navigate_home()
                                            sleep(randint(10, 30))
                                        count_url_change += 1

                            # Modifies DataFrame's data in column 'Group Type',
                            # and saves changes to csv
                            df2 = pd.DataFrame(group_types, columns=[r"Group Type"])
                            df[r"Group Type"] = df2[r"Group Type"]
                            df.to_csv(os.path.join(SAVE_PATH, f_name), sep=',',
                                      mode='w', index=False)

                sleep(randint(2, 5))
                # Closes the current window of the WebDriver.
                self.driver.close()

                # Fixes preference in Chrome User Data -
                # Enables JavaScript back
                enable_js_preference()

    def parse_groups(self):
        """
        Parse data from crawled facebook URLs,
        and saves it to a csv / text file.
        :return:
        """
        if self.p_sources_list:
            # get the current local datetime formatted to a day,
            # month, year, hour, and minute
            current_time = datetime.strftime(datetime.today(), "%d_%m_%y#%H-%M")

            for sources in self.p_sources_list:
                if len(sources) == 3:
                    target_id = sources[0]  # uid of the fb target
                    source = sources[1]  # profile's groups HTML source
                    public_source = sources[2]  # profile's public groups HTML source

                    if source and target_id:
                        # Finds all groups <a> tags and groups' members, using re library
                        all_groups_data = find_data_with_re(source, "all_groups")
                        members_data = find_data_with_re(source, "members")

                        profile_name = ""
                        public_groups_links = []
                        if public_source:
                            # Finds public groups <a> tags, and parses the links,
                            # using re library
                            public_groups_data = find_data_with_re(public_source,
                                                                   "all_groups")
                            if public_groups_data:
                                for i in range(len(public_groups_data)):
                                    public_group_link = find_data_with_re(public_groups_data[i],
                                                                          "public_group_link")
                                    if public_group_link:
                                        public_groups_links.append(public_group_link.group(1))

                            # BeautifulSoup obj to parse some HTML
                            soup = BeautifulSoup(public_source, 'html.parser')
                            # parsing profile name from timeline title (in group section)
                            profile_name = soup.title.string

                        if not profile_name:
                            # parsing profile name from search results page
                            # (search/[FID}/groups)
                            soup = BeautifulSoup(source, 'html.parser')
                            profile_name = profile_names_from_title(soup)

                        parsed_data = []
                        counter = 0
                        for i in range(len(all_groups_data)):
                            # Parses group link and name, using re library
                            group_link = find_data_with_re(all_groups_data[i],
                                                           "group_link")
                            group_name = find_data_with_re(all_groups_data[i],
                                                           "group_name")

                            if group_link and group_name:
                                group_type = "Unknown"
                                members = ""
                                if members_data and counter < len(members_data):
                                    members = members_data[counter]
                                counter += 1

                                g_link = group_link.group(1)
                                link_text = group_name.group(1)

                                # Changes the group's privacy, if the group
                                # appears also in public groups section
                                if public_groups_links:
                                    group_type = "Closed Group"
                                    if g_link in public_groups_links:
                                        group_type = "Public Group"

                                # Replacing all commas with spaces in group name -
                                # so csv columns will be ordered
                                if "," in link_text:
                                    link_text = link_text.replace(",", "-")

                                # append required parameters (uid, name, link text,
                                # group link, group members, group type/privacy,
                                # current time)
                                parsed_data.append([target_id, profile_name, link_text,
                                                    FB_URL+g_link, members, group_type,
                                                    current_time])

                        # Saving Groups Data
                        tmp_file_name = os.path.join(SAVE_PATH, target_id + "#groups#" +
                                                     current_time+'.csv')
                        if parsed_data:
                            # Saves data to a csv file
                            save_with_pandas(parsed_data, GROUP_COLUMNS, tmp_file_name)
                        else:
                            # Checks if there are no results (for the desired query)
                            # and saves to text file
                            soup = BeautifulSoup(source, 'html.parser')
                            check_results(soup, tmp_file_name, profile_name, target_id)


def find_data_with_re(source, x):
    """
    Using regular-expressions to find web elements / match strings
    :param source: string
    :param x: query, for choosing function with re library (string)
    :return: calls regular-expressions function by the desired query (list)
    """
    return {
        "all_groups": re.findall(r'<a[^<]+\/groups\/[^<]+</a>', source),
        "members": re.findall(r'[\d\.K,]+(?= member)', source),
        "group_link": re.match(r'.+(\/groups\/[^\/]+)\/(?=\?ref=br_rs)', source),
        "public_group_link": re.match(r'.+(\/groups\/[^\/]+)\/(?=")', source),
        "group_name": re.match(r'.+>(.+)</a>', source),
    }[x]


def profile_names_from_title(soup):
    """
    :param soup: BeautifulSoup Object (with the
    required page source)
    :return: profile name (string)
    """
    title = soup.title.string
    split_s = title.split("'s")
    split_by = title.split(" by ")
    split_of = title.split(" of ")
    if split_s:
        return split_s[0]
    if split_by:
        return split_by[1].strip(" - Facebook Search")
    if split_of:
        return split_of[1].strip(" - Facebook Search")
    return None


def save_with_pandas(parsed_data, columns, file_name):
    """
    Saves groups' data to csv file with pandas
    :param parsed_data: parsed data from Group Scraper (list)
    :param columns: Columns to set in panda's DataFrame (list)
    :param file_name: string
    """
    df = pd.DataFrame(parsed_data, columns=columns)
    if not df.empty:
        df.to_csv(file_name, sep=',', encoding='utf-8-sig', index=False)


def check_results(soup, file_name, profile_name, target_id):
    """
    Checks if there are no results (for the desired query), and saves to text file
    :param soup: BeautifulSoup Object
    :param file_name: string
    :param profile_name: string
    :param target_id: string
    """
    no_results = soup.find(text="We couldn't find anything for")
    no_results2 = soup.find(text="Looking for people or posts? Try entering a name, "
                                 "location, or different words.")
    # no results in html page source
    if no_results or no_results2:
        file_name = file_name.replace(".csv", ".txt")
        with codecs.open(file_name, 'w', encoding='utf-8') as out_f:
            out_f.write("No Results, probably because :\n")
            out_f.write("1) There are no results for the desired query - "
                        + GROUPS_URL.replace("[FID]", target_id) + "\n")
            if profile_name:
                out_f.write("2) The Profile, " + profile_name
                            + " (FID="+target_id+"), has no groups!")
            else:
                out_f.write("2) The Profile - "+"FID="+target_id+", has no groups!")


def sort_files_by_size(files_list, tmp_path):
    """
    Sort Files from a given path by their size
    :param files_list: list - required files to sort by their size
    :param tmp_path: String - The desired path
    :return: list - sorted files' names
    """
    sorted_files = []
    if files_list:
        # Loop and add files to list
        pairs = []
        for f in files_list:
            # Get size and add to list of tuples
            size = os.path.getsize(os.path.join(tmp_path, f))
            pairs.append((size, f))
        # Sort list of tuples by the first element, size.
        pairs.sort(key=lambda s: s[0])
        # Loop and add sorted files' names to list
        for i in range(len(pairs)):
            sorted_files.append(pairs[i][1])
    return sorted_files


def create_dir(path):
    """
    Creates directories (if not exist)
    :param path: path for directories creation (string)
    """
    if not os.path.exists(path):
        os.makedirs(path)


def nodes_from_groups():
    """
    Creates Nodes and Relationships with neo4j(graph db) using py2neo,
    to store/visualize all parsed group data from csv files on db
    :return:
    """
    try:
        # a list of paths matching a pathname pattern.
        csv_files = glob.glob1(SAVE_PATH, "*.csv")
        if csv_files:
            # The 'Graph' class represents the graph data storage space within
            # a Neo4j graph database. Connection details are provided using URIs
            # and/or individual settings.
            graph = Graph(uri="bolt://localhost:7687", user="neo4j", password=NEO_PASSWORD)
            # Begin a new 'Transaction' - a logical container for multiple
            # Cypher statements.
            tx = graph.begin()

            relation = "MEMBER_IN"  # relationship string
            group_type = "Group"  # string for node label (group privacy/type)
            for f_name in csv_files:
                # opens a csv file with pandas
                df = pd.read_csv(os.path.join(SAVE_PATH, f_name))
                # df is not empty
                if not df.empty:
                    ok_to_create = True
                    for column in GROUP_COLUMNS:
                        if column not in df:
                            # expected column is not found on the dataframe
                            ok_to_create = False
                            break

                    # creates node and relationships to Neo4j GDB
                    if ok_to_create:
                        prof_name = str(df[r"Profile Name"][0])  # fb profile name
                        prof_id = str(df[r"UID"][0])  # fb profile uid
                        # create a 'person' Node with given details
                        pers_node = Node("Person", name=prof_name, uid=prof_id)

                        # Merge node into the database. The merge is carried out
                        # by comparing that node with a potential remote equivalent
                        # on the basis of a label and property value. If no remote
                        # match is found, a new node is created.
                        graph.merge(pers_node)

                        # iterates pandas df
                        for index, row in df.iterrows():
                            # check string inside row[r"Group Type"] and sets a string
                            # for node label (group privacy/type)
                            if "Public" in row[r"Group Type"]:
                                group_type = "Public Group"
                            elif "Closed" in row[r"Group Type"]:
                                group_type = "Closed Group"

                            # create a 'Group' OR 'Public Group' OR 'Closed Group' Node
                            # with given details (group name, groupID, group members)
                            group_node = Node(group_type,
                                              name=row[r"Group Name"],
                                              group_id=row[r"Group ID"],
                                              members=row[r"Members"])
                            if group_node:

                                # Merge node into the database. The merge is carried out
                                # by comparing that node with a potential remote equivalent
                                # on the basis of a label and property value. If no remote
                                # match is found, a new node is created.
                                graph.merge(group_node)

                                # Merge relationship into the database. the merge is carried
                                # out by comparing that relationship with a potential remote
                                # equivalent on the basis of matching start and end nodes
                                # plus relationship type. If no remote match is found,
                                # a new relationship is created.
                                graph.merge(Relationship(pers_node, relation, group_node))
            # Commit the transaction.
            tx.commit()
    except:
        print("Forgot to connect NEO4J server! Or a problem occurred with data")
        pass


def enable_js_preference():
    """
    fixes problem that enforces javascript to be disabled on browser as default
    (remove this setting from text file)
    :return:
    """
    #  Open file and return a stream
    f = open(os.path.join(PREFERENCES_PATH, 'Preferences'), "r+")
    # Read and return a list of lines from the stream.
    txt_lines = f.readlines()
    # Change stream position to to start
    f.seek(0)
    for line in txt_lines:
        if r',"managed_default_content_settings":{"javascript":2}' in line:
            # Write string to stream - remove the javascript
            # default setting ("javascript":2 -> means disabled):
            # ',"managed_default_content_settings":{"javascript":2}'
            f.write(line.replace(r',"managed_default_content_settings":{"javascript":2}', ''))
        else:
            # Write string to stream
            f.write(line)
    # Truncate file to size bytes.
    f.truncate()
    # Flush and close the IO object.
    f.close()


def main():
    """
    The main Function that runs GUI and Facebook profiles' Groups Scraper
    :return:
    """
    # Fixes preference in Chrome User Data - Enables JavaScript back
    enable_js_preference()
    g = GuiMenu()  # Tk GUI Object

    # list of user's ids to crawl their groups
    targets_list = g.profiles_lst
    # option to check group with unknown privacy (boolean)
    unknown_groups_privacy_q = g.is_unknown_groups_q
    # option to to store/visualize all parsed group data from csv files
    # on Neo4J GDB (boolean)
    visualize_neo_q = g.is_visualize_neo

    is_sleep = False
    if targets_list:
        # init 'GroupsScraper' obj and crawls facebook targets'
        # groups data (public and/or private)
        scraper = GroupsScraper(targets_list, True)
        scraper.crawl_groups()

        # Parsing HTML data of profile's groups (with BeautifulSoup
        # and re library)
        scraper.parse_groups()
        is_sleep = True

    if unknown_groups_privacy_q:
        # Crawls all groups (with unknown privacy), with a deeper search -
        # get groups' type (Public, Private) directly from the group page
        if is_sleep:
            # delay between requests through WebDriver
            sleep(randint(2*60, 5*60))

        # init 'GroupsScraper' obj
        scraper_g = GroupsScraper(None, False)
        # crawl given fb groups' web pages directly to find their
        # privacy status (Closed/Public)
        scraper_g.groups_privacy_deep_search()

    if visualize_neo_q:
        # store data of profiles' groups to Neo4J GDB
        nodes_from_groups()
        run_neo_server()

if __name__ == '__main__':
    main()
