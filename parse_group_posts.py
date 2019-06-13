"""The program gets KeyWords and fb group urls as an input
(through Tkinter GUI), to scrape groups' data and posts details, and then
generates csv reports as an output. The process is based on tools like
selenium webdriver, beautifulsoup, re - to scrape the web & parse some html.

This is an old, basic and messy code that I have written for educational purposes.
*You may see more details on the README.md file.

## output details (that the script extract from fb groups' posts) may include:
'Group Name, 'Group URL', 'Members', 'Group Type', 'Post'(content), 'Post Title',
'Uploader Name', 'Uploader URL', 'Upload Time', 'Post Likes', 'Post Comments', 'Time Stamp',
and 'KeyWords' count of matches within each post.

## Disclaimer:
The scripts / tools are for educational purposes only,
and they might violate some websites (including social media) TOS.
Use at your own risk."""
import pandas as pd
from tkinter.filedialog import *
from tkinter.scrolledtext import *
from selenium import webdriver
from selenium.common.exceptions import *
from bs4 import BeautifulSoup
from datetime import *
from time import sleep
from random import randint


# -*- coding: UTF-8 -*-
__author__ = "KnifeF"
__license__ = "MIT"
__email__ = "knifef@protonmail.com"

# ****************************************WebDriver Settings / other parameters*****************************
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
SAVE_PATH = os.path.join(os.environ["HOMEPATH"], "DESKTOP", "group_posts")
# columns of output csv files
GROUP_COLUMNS = [r"Group Name", r"Group URL", r"Members", r"Group Type", r"Post",
                 r"Post Title", "Uploader Name", r"Uploader URL", "Upload Time",
                 r"Post Likes", r"Post Comments", r"Time Stamp"]
FACEBOOK = "https://www.facebook.com"  # basic fb url
FB_URL2 = "https://mbasic.facebook.com"  # basic fb url for mobile when js is disabled
# xpath for a link/button that contains 'Groups' as text
GROUPS_BTN = r"//a[text()[contains(.,'Groups')]]"
# xpath for a link/button that contains 'Home' as text
HOME_BTN = r"//a[text()[contains(.,'Home')]]"
# xpath for a link/button that contains 'See More Posts' as text
SEE_MORE_POSTS = r"//*[text()[contains(.,'See More Posts')]]"
# is used as a 'see more' button clicks limit
SEE_MORE_CLICK_LIMIT = 20


# ****************************************GUI Functions*****************************************************
class GuiMenu(Tk):
    """
    Tk GUI object as 'GuiMenu' for launching the 'GroupsCrawler'
    """
    def __init__(self):
        """
        Builds a Tk GUI object ('GuiMenu') with required parameters
        """
        super().__init__()
        self.title("Crawler")
        self.resizable(0, 0)
        # self.iconbitmap(r'Facebook.ico')
        self.config(background="#3b5998")
        self.keywords = []
        # *******************************Menu*********************************
        menu = Menu(self)
        file_menu = Menu(menu)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open...", command=self.open_file)
        file_menu.add_command(label="Clear Text", command=self.clear_text)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        self.config(menu=menu)
        # *******************************Labels*******************************
        Label(self, text="Groups Crawler", background='#3b5998',
              foreground='white', font=("Lucida Grande", 20, 'bold')).pack()
        Label(self, text="Please Enter KeyWords To Search:",
              background='#3b5998',  foreground='white',
              font=("Lucida Grande", 10, 'italic')).pack()
        # ****************************Scrolled Text***************************
        self.text = ScrolledText(self, background='white', foreground='black',
                                 insertbackground="black",
                                 font=("Lucida Grande", 10),
                                 width=25, height=5)
        self.text.pack()
        # *******************************Buttons******************************
        Button(self, text='Quit', background="#3b5998", foreground="white",
               font=("Lucida Grande", 12, 'bold'), command=self.destroy)\
            .pack(side=RIGHT)
        Button(self, text='Scrape Groups!', background="#3b5998",
               foreground="white", font=("Lucida Grande", 12, 'bold'),
               command=self.keywords_to_lst).pack(side=RIGHT)

        mainloop()

    def keywords_to_lst(self):
        """
        Creates list with entered profiles (ScrolledText),
        and exits GUI window
        :return:
        """
        if self.text:
            lines_from_text = (self.text.get(0.0, END)).split("\n")
            for row in lines_from_text:
                key_w = row.strip()
                ok = (key_w is not "") and (key_w is not " ")
                if ok:
                    self.keywords.append(key_w)
            if self.keywords:
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


# ****************************************Groups Crawler Functions******************************************
class GroupsCrawler:
    """
    GroupsCrawler handles the scraping process of fb groups' posts data
    (scraping groups content and posts' details)
    """
    def __init__(self, groups_to_check, keywords):
        """
        Builds object that handles fb groups' posts scraping process
        (of fb groups targets)
        :param groups_to_check: groupIDs to crawl (list)
        :param keywords: keywords to search in groups' posts (list)
        """
        self.groups_to_check = groups_to_check
        self.keywords = keywords

        # Set chromedriver to the desirable mode
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(WITHOUT_EXTENSIONS)
        chrome_options.add_argument(ARGUMENTS)
        chrome_options.add_experimental_option("prefs", JS_PREFERENCE)
        # Creates a new instance of the chrome driver.
        self.driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH,
                                       chrome_options=chrome_options)
        # Maximizes the current window that webdriver is using
        self.driver.maximize_window()

        # create dirs in given path
        create_dir(SAVE_PATH)

    def navigate_home(self):
        """
        navigates from the current facebook page to facebook's
        home page (main page)
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

    def groups_posts_deep_search(self):
        """
        scraping some groups' posts data
        :return:
        """
        # list that includes HTML pages' sources of fb groups
        all_htm = []
        # Navigates to facebook url (in a mobile version -
        # without JavaScript)
        self.driver.get(FB_URL2)

        # Set time to sleep (delay)
        max_sleep = 90
        if len(self.groups_to_check) > 40:
            max_sleep = 4*60  # increase time to sleep
        old_group_title = ""

        # iterate over urls of facebook groups
        for index in range(len(self.groups_to_check)):
            sleep(randint(5, 20))  # shorter sleep
            if index > 0:
                sleep(randint(20, max_sleep))  # longer sleep

            # get current url string from list
            group_url = self.groups_to_check[index]
            # Navigates to facebook group URL (mobile version)
            self.driver.get(group_url)
            sleep(randint(10, 30))

            new_group_title = self.driver.title  # the title of the current page
            if new_group_title != old_group_title:  # Checks if the title have changed
                old_group_title = new_group_title

                # Find specific element by id - indicates a group's facebook page
                groups_stories_elems = self.driver\
                    .find_elements_by_id("m_group_stories_container")

                sleep(3)  # delay

                # Find specific element css selector - indicates that
                # the group has posts
                post_elems = self.driver\
                    .find_elements_by_css_selector("div[role='article']")

                if groups_stories_elems and post_elems:
                    # append WebDriver pages source to list
                    all_htm.append(self.driver.page_source)
                    # loop that clicks on 'See more posts' button
                    # in a facebook group, and appends HTML pages'
                    # sources to list
                    all_htm = self.see_more_loop(all_htm)
                    if all_htm:
                        # parsed the relevant data from the facebook group
                        self.parse_groups(group_url, all_htm)
                        sleep(randint(10, 60))

            # Decides randomly to navigates home
            to_home = randint(1, 4)
            if to_home == 3:
                self.navigate_home()

        sleep(randint(2, 5))
        # close selenium WebDriver's current window.
        self.driver.close()
        # Fixes preference in Chrome User Data - Enables JavaScript back
        enable_js_preference()

    def see_more_loop(self, all_htm):
        """
        Loop that clicks on 'show more' to get more data from
        a facebook page (javascript disabled)
        :param all_htm: includes HTML pages' sources of fb groups (list)
        :return:
        """
        # Finds multiple elements by xpath.
        see_more_elem = self.driver.find_elements_by_xpath(SEE_MORE_POSTS)
        count = 0
        # 'find_elements_by_xpath' returns list of WebElement
        # that is not empty
        while see_more_elem:
            try:
                sleep(randint(4, 12))
                # clicks button/link
                see_more_elem[0].click()
                count += 1
                sleep(randint(2, 4))
                # append the source of the current page (through the WebDriver)
                # to a list
                all_htm.append(self.driver.page_source)
                sleep(randint(1, 3))
                # Finds multiple elements by xpath.
                see_more_elem = self.driver.find_elements_by_xpath(SEE_MORE_POSTS)
                # break loop if there are more than the given limit
                # of 'see more' button clicks
                if count > SEE_MORE_CLICK_LIMIT:
                    break
            except WebDriverException:
                print("WebDriverException")
                pass
        return all_htm

    def parse_groups(self, group_url, all_htm):
        """
        Parse html data from crawled facebook groups URLs,
        and saves it to a csv / text file.
        :param group_url: current crawled url of a facebook group (str)
        :param all_htm: list that includes HTML sources of crawled
        facebook web pages of groups (list)
        :return:
        """
        parsed_data = []
        # get the current local datetime formatted to a day, month, year,
        # hour, and minute
        current_date = datetime.strftime(datetime.today(), "%d_%m_%y#%H-%M")
        if all_htm:
            # BeautifulSoup obj to parse some HTML
            soup = BeautifulSoup(all_htm[0], 'html.parser')
            # parse the name of the group
            group_name = soup.title.string
            # change fb group url to include the basic fb url
            # (instead of the mobile version url)
            group_url = group_url.replace(FB_URL2, FACEBOOK)
            # parse the number of members in the groups
            members = ret_members(soup)
            # parse group type (closed or open)
            group_type = ret_group_type(all_htm[0])

            # iterates list to parse each HTML source of a fb group crawled web data
            for htm in all_htm:
                # BeautifulSoup obj to parse some HTML
                soup = BeautifulSoup(htm, 'html.parser')
                # using 'find_all' to extract a list of Tag objects that match the
                # given criteria. (posts' data should be within these tags)
                articles_elems = soup.find_all("div", {"role": "article"})
                # a list of Tag objects that match the given criteria is found
                if articles_elems:
                    for div in articles_elems:
                        # parse passed time since the post have been uploaded
                        post_upload_time = ret_upload_time(div)
                        # parse likes on post
                        post_likes = ret_post_likes(div)
                        # parse comments on post
                        post_comments = ret_post_comments(div)

                        # extract text of the 'div' tag
                        div_text = div.getText()
                        if div_text:
                            # find 'h3' tag in 'div' tag
                            title_elem = div.find("h3")
                            if title_elem:
                                # parse title of post
                                post_title = title_elem.getText()
                                # parse uploader Name & URL
                                uploader_name, uploader_url = ret_uploaded_by(title_elem)

                                # parse written paragraphs from post
                                p_tags = div.find_all("p")
                                post_text = ""
                                for p in p_tags:
                                    # extract text from a 'p' tag
                                    post_text += p.getText()+"\n"

                                # post text (str) is not empty
                                if post_text:
                                    tmp_lst = []
                                    # iterate over the given list of KW to search
                                    # within the post text
                                    for keyword in self.keywords:
                                        # Returns a list of all non-overlapping matches in the
                                        # string ('post_text'). The pattern to find is the
                                        # current keyword from list of keywords.
                                        # Then, Appends the length of the returned list (=count
                                        # of repeated occurrences of the KW) to another list
                                        tmp_lst.append(len(re.findall(r'%s' % keyword, post_text)))

                                    # check whether an upload time for this post is found
                                    if post_upload_time:
                                        # append data of a group's post to a list
                                        # the data includes: group name, group url, members,
                                        # type/privacy (Public/Closed), post's text, post's title,
                                        # post's uploader name & url, upload time, likes count,
                                        # comments count, current date&time, and a list with count
                                        # of the occurrences of given keywords within the post.
                                        parsed_data.append([group_name, group_url, members,
                                                            group_type, post_text.replace("\n", ". "),
                                                            post_title, uploader_name, uploader_url,
                                                            post_upload_time, post_likes, post_comments,
                                                            current_date] + tmp_lst)
            # list is not empty
            if parsed_data:
                # remove special characters from 'group_name' (str), that as a
                # part of the filename, it won't corrupt the file creation process.
                group_name_filter = re.sub(r'[(){}<>.#$!@|%^&*,:+~`;]', '', group_name)

                # path for the output .csv file (to store parsed fb group's posts data)
                tmp_file_name = os.path.join(SAVE_PATH, group_name_filter +
                                             "#group_posts#"+current_date+'.csv')

                # using pandas DataFrame to organize the given parsed data,
                # and to store the DataFrame to a csv file
                save_with_pandas(parsed_data, tmp_file_name, self.keywords)


def save_with_pandas(parsed_data, tmp_file_name, keywords):
    """
    using pandas DataFrame to organize the given parsed data
    by specified columns/order/structure, and to store the DataFrame
    (with some fb group's posts data) to a CSV file.
    :param parsed_data: parsed data that includes some fb group's posts
    data (list)
    :param tmp_file_name: path for the output .csv file -(str)
    :param keywords: keywords to find within group's posts (list)
    :return:
    """
    # create a pandas DataFrame with the parsed data, and specified columns.
    df = pd.DataFrame(parsed_data, columns=GROUP_COLUMNS+keywords)
    # pandas DataFrame is not empty
    if not df.empty:
        # Write DataFrame to a comma-separated values (csv) file,
        # with a given file path, 'sep' (field delimiter),
        # 'encoding', and 'index' params.
        df.to_csv(tmp_file_name, sep=',', encoding='utf-8-sig', index=False)


def ret_group_type(source):
    """
    check a fb group's type/privacy status (Closed/Public)
    from given HTML page source (from web page of fb group).
    :param source: an HTML page source (str)
    :return: group's type/privacy status -
    Public Group/Closed Group/Unknown (str)
    """
    # Return a list of all non-overlapping matches
    # in the string 'source' (the pattern to find
    # is 'Public Group')
    is_public = re.findall(r'Public Group', source)
    # Return a list of all non-overlapping matches
    # in the string 'source' (the pattern to find
    # is 'Closed Group')
    is_closed = re.findall(r'Closed Group', source)
    # 'Public Group' pattern is found
    if is_public:
        return "Public Group"
    # 'Closed Group' pattern is found
    if is_closed:
        return "Closed Group"
    # patterns are not found (failed to detect the
    # privacy of the fb group)
    return "Unknown"


def ret_uploaded_by(title_elem):
    """
    parse uploader of the given post (uploader name & url)
    :param title_elem: a Tag object (<h3>) - should include
    data about the uploader of the post
    :return: post's uploader name & url, that should be inside
    an <h3> tag (str)
    """
    # Return only the first child of this Tag matching the
    # given criteria. find an 'a' tag.
    a_tag = title_elem.find("a")
    # check if an 'a' Tag object is found, and has an
    # 'href' attribute
    if a_tag and a_tag.has_attr('href'):
        # uploader url should be within the 'href' attr
        uploader_url = a_tag['href']
        # check whether there is a need to remove a url
        # reference / query at the end of the string
        if "?fref" in uploader_url:
            uploader_url = uploader_url.split("?fref")[0]
        elif "&fref" in uploader_url:
            uploader_url = uploader_url.split("&fref")[0]
        elif "?refid" in uploader_url:
            uploader_url = uploader_url.split("?refid")[0]
        elif "&refid" in uploader_url:
            uploader_url = uploader_url.split("&refid")[0]
        # should return the name of the post's uploader,
        # and a url that links to his fb profile
        return a_tag.getText(), FACEBOOK+uploader_url
    return None, None


def ret_post_comments(div):
    """
    parse comments on given post
    :param div: a Tag object (<div>) that should include post data
    :return: comments count on given post, that should be inside
    a <div> tag (str)
    """
    # Extracts a list of Tag objects that match the given criteria.
    # find all 'a' tags that include the text 'Comment'
    a_tags = div.find_all("a", text=re.compile('Comment'))
    for comments_elem in a_tags:
        # re pattern to find comment count inside element's text
        # the pattern may include a decimal num, 'K' for represent a thousand,
        # and ' Comment' should be at the end of the string
        comments = re.findall(r'[\d.K,]+(?= Comment)', comments_elem.getText())
        if comments:
            # should be the comment count on the given post
            return comments[0]
    return None


def ret_post_likes(div):
    """
    parse likes on given post
    :param div: a Tag object (<div>) that should include post data
    :return: likes count on given post, that should be inside
    a <div> tag (str)
    """
    # Extracts a list of Tag objects that match the given criteria.
    # find all 'a' tags
    a_tags = div.find_all("a")
    for a_tag in a_tags:
        # checks if current a tag (from list of Tag objects) has
        # an 'aria-label' attribute
        if a_tag.has_attr("aria-label"):
            # tag's text should be the likes count
            return a_tag.getText()
    return None


def ret_upload_time(div):
    """
    parse passed time since the post have been uploaded
    :param div: a Tag object (<div>) that should include post data
    :return: upload time of given post, that should be inside
    a <div> tag (str)
    """
    # Extracts a list of Tag objects that match the given criteria.
    # find all 'abbr' tags
    date_elems = div.find_all("abbr")
    if date_elems:
        # text of the first element in the list
        # should be the upload time
        return date_elems[0].getText()
    return None


def ret_members(soup):
    """
    parse the members count of the fb group from BeautifulSoup obj
    (that is built with HTML source of fb group web page)
    :param soup: BeautifulSoup obj
    :return: members count of the fb group (str)
    """
    # Return only the first child of this Tag matching the
    # given criteria. find a 'td' tag which includes
    # the string 'Members'.
    members_elem = soup.find("td", string="Members")
    # 'td' tag object (with the string 'Members') is found,
    # and has a 'parent' element
    if members_elem and members_elem.parent:
        # extract the text from the 'parent' element, and removes
        # the 'Members' string to include only the members count.
        return members_elem.parent.getText().replace("Members", "")
    return None


def create_dir(path):
    """
    Creates directories (if not exist)
    :param path: path for directories creation (string)
    """
    if not os.path.exists(path):
        os.makedirs(path)


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
            # Write string to stream - remove the javascript default setting (2 means disabled):
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
    The main Function that runs GUI and fb groups' posts scraper
    :return:
    """
    # Fixes preference in Chrome User Data - Enables JavaScript back
    enable_js_preference()

    groups_to_check = ["https://mbasic.facebook.com/groups/[grupID1]/",
                       "https://mbasic.facebook.com/groups/[grupID2]/"]

    g = GuiMenu()  # Tk GUI Object
    # list of user's keywords to search within crawled fb groups' posts
    keywords = g.keywords
    if keywords:
        # Builds object that handles fb groups' posts scraping
        # process (of fb groups targets)
        scraper = GroupsCrawler(groups_to_check, keywords)
        # Crawls facebook groups' posts and some other details
        scraper.groups_posts_deep_search()

if __name__ == '__main__':
    main()
