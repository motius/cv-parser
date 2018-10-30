import os
import subprocess

from selenium import webdriver


class Scraper:
    """WebDriver used for opening, rendering, and scraping HTML files."""

    def __init__(self):
        chromedriver = os.path.dirname(os.path.abspath(__file__)) + "/webdriver/chromedriver"
        os.environ["webdriver.chrome.driver"] = chromedriver
        self.browser = webdriver.Chrome(chromedriver)
        self.browser.set_window_position(-100000, 0)  # move browser window out of screen

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.browser.close()


def convert_pdf_to_html(file_path):
    """"Converts the file to HTML to PDF and returns the path.
    The returned value is None if the file could not be converted."""

    path_of_generated_html = os.path.splitext(file_path)[0] + ".html"
    directory_of_file = os.path.dirname(os.path.abspath(path_of_generated_html))
    if not os.path.exists(path_of_generated_html):
        if execute_pdf_to_html_process(file_path, directory_of_file) is not 0:
            print('The file ' + file_path + " can't be converted to html. Sorry.")
            return None
    return path_of_generated_html


def execute_pdf_to_html_process(filename, destination_dir=None):
    """Converts the PDF file specified by filename to PDF file, by calling the pdf2htmlEX
    in a separate 'terminal process'. Optionally puts it in the destination_dir. If destination_dir
     is empty, the execution folder is used, i.e. the folder in which the pdf was found."""

    if destination_dir is None:
        destination_dir = os.path.dirname(filename)
        command = "pdf2htmlEX --dest-dir " + destination_dir + " --optimize-text 1 " + filename
    else:
        command = "pdf2htmlEX --dest-dir " + destination_dir + " --optimize-text 1 " + filename
    process_status_code = subprocess.call(command, shell=True)
    return process_status_code


def convert_html_resume_to_object(path_to_html):
    """Parses the html resume line by line into a list of "line dictionaries".
    For each line the font-type, font-size, left-margin, font-color, page-number
    and text are extracted and stored in a dict. At the end the list of dictionaries is returned."""

    scraper = Scraper()
    url_to_file = "file:///" + path_to_html
    scraper.browser.get(url_to_file)

    resume_lines = []

    page_container = scraper.browser.find_element_by_id("page-container")
    for page in page_container.find_elements_by_class_name("pf"):
        # Scroll with the browser to the page to make the page (dynamically) render.
        scraper.browser.execute_script("arguments[0].scrollIntoView();", page)
        for line in page.find_elements_by_class_name("t"):
            line_props = get_line_properties(line)
            line_props['page_number'] = page.get_attribute("data-page-no")
            resume_lines.append(line_props)
    return resume_lines


def get_line_properties(line):
    """Takes a html (line) element as a input and puts its details (font-size, font-family, left-margin, text-color
    and text) into a dictionary. Thus creating a dictionary that contains the text and its visual properties."""

    font_size = line.value_of_css_property("font-size")
    font_family = line.value_of_css_property("font-family")
    left_margin = get_corrected_left_margin(line)

    font_color = line.value_of_css_property("color")
    bottom_margin = line.value_of_css_property("bottom")
    text = line.text
    return {
        'font_size': font_size,
        'font_family': font_family,
        'left_margin': left_margin,
        'font_color': font_color,
        'bottom_margin': bottom_margin,
        'line_text': text,
        'page_number': 0
    }


def get_corrected_left_margin(line):
    """Unfortunately in some cases a "tabbing" is not identified by the pdf -> html converter properly, and instead
    of giving the correct left-margin, the converter assigns an incorrect left margin and adds many blank spaces
    to the beginning of the text. Example:

    Work Experinece:
              .....
              Internship
    Now if internship is written with the font-size/color etc. of section keywords, it will be recognized as section keyword,
    meanwhile in reality its left margin shouldn't mach the left margin of section keywords.

    The function looks into such cases and increases the left margin value for such lines. The amount is not relevant,
    only the fact, that it has significantly higher left-margin, hence the multiplication with 5"""

    left_margin_value = line.value_of_css_property("left")
    text = line.text
    if text[:5].strip() == "":
        left_margin_value = float(left_margin_value[:-2]) # Remove the px post-script
        left_margin_value *= 5
        left_margin_value = str(left_margin_value) + "px"
    return left_margin_value