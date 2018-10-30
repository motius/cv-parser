import re
from .textCleaners import clean_text


class DateRegex:
    """DateRegex class used to find the a duration (specified by two dates) in various formats."""
    not_alpha_numeric = r'[^a-zA-Z\d]'

    # Various month format definitions
    months_short = r'(jan)|(feb)|(mar)|(apr)|(may)|(jun)|(jul)|(aug)|(sep)|(oct)|(nov)|(dec)'
    months_long = r'(january)|(february)|(march)|(april)|(may)|(june)|(july)|(august)|(september)|(october)|(november)|(december)'
    months_numeric = r'(?<![\d])\d{1,2}(?![\d])'
    month_alphabetic = r'(' + months_short + r'|' + months_long + r')'
    month_numeric_long = r'([\d]{1,2})(?=[^A-Za-z]{1}[\d]{4})'

    year = r'((20|19)(\d{2}))'
    # Double (normal) year range (e.g.: 2013 - 2014)
    double_year_range = year + not_alpha_numeric + r"{1,3}" + year

    # Multi year range (e.g.: 2013 - 2014 - 2015)
    multi_year_range = r'(' + year + '(' + not_alpha_numeric + r'{1,3}' + year + '){1,5})|(' + year +\
                       not_alpha_numeric + r'{1,3}' + r')'

    # Start Date definitions in various formats
    start_date_alphabetic = month_alphabetic + not_alpha_numeric + r"{1,3}" + year
    start_date_numeric = months_numeric + not_alpha_numeric + r'{1,3}' + year
    start_date_numeric_long = r'[\d]{1,2}[^a-zA-Z\d]?' + months_numeric + not_alpha_numeric + r'?' + year
    start_date_alphabetic_long = r'[\d]{1,2}[^a-zA-Z\d]?' + month_alphabetic + not_alpha_numeric + r'?' + year

    # End Date definitions in various formats
    end_date_alphabetic = r'((' + month_alphabetic + not_alpha_numeric + r"{1,3}" + year + r')|(present)|(now)|(today))'
    end_date_numeric = r'((' + months_numeric + not_alpha_numeric + r"{1,3}" + year + r')|(present)|(now)|(today))'
    end_date_numeric_long = r'(([\d]{1,2}[^a-zA-Z\d]?' + months_numeric + not_alpha_numeric + r"?" + year + r')|(present)|(now)|(today))'
    end_date_alphabetic_long = r'(([\d]{1,2}[^a-zA-Z\d]?' + month_alphabetic + not_alpha_numeric + r"?" + year + r')|(present)|(now)|(today))'

    # Date Range alphabetic (e.g.: April 2013 - May 2014)
    date_range_alphabetic = r"(" + start_date_alphabetic + not_alpha_numeric + r"{1,3}" + end_date_alphabetic + r")|(" + double_year_range + r")"

    # Date Range numberic (e.g.: 01.2014 - 12.2014)
    date_range_numeric = r"(" + start_date_numeric + not_alpha_numeric + r"{1,3}" + end_date_numeric + r")"
    # Date Range numeric long format (e.g.: 15.01.2014 - 31.07.2015)
    date_range_numeric_long = r"(" + start_date_numeric_long + not_alpha_numeric + r"{1,3}" + end_date_numeric_long + r")"
    # Date Range alphabetic long format (e.g.: 15. May 2015 - 16. July 2017)
    date_range_alphabetic_long = r"(" + start_date_alphabetic_long + not_alpha_numeric + r"{1,3}" + end_date_alphabetic_long + r")"

    # MM.YYYY-MM.YYYY Date range in either alphabetic or numeric format
    date_range = r'(' + date_range_alphabetic + r'|' + date_range_numeric + r')' + r'(' + not_alpha_numeric + r'{1,4}|$)'
    # DD.MM.YYYY - DD.MM.YYYY Date range in numeric format
    date_range_long_numeric = r'(' + date_range_numeric_long + r')' + not_alpha_numeric + r'{1,4}'
    # DD.MM.YYYY - DD.MM.YYYY Date range in alphabetic format
    date_range_long_alphabetic = r'(' + date_range_numeric_long + r')' + not_alpha_numeric + r'{1,4}'

    # Open-ended durations, where only start date is present (e.g: 2.2015 - )
    start_date_only = r'(?<![^A-Za-z]{5})' + r'(' + start_date_numeric + r'|' + start_date_alphabetic + r')' + r'(?![^A-Za-z]{5})'

    # Month range (e.g.: From 02-04 2014 finds 02-04)
    month_range = r'(' + month_alphabetic + r'|' + months_numeric + r')' + not_alpha_numeric + r"{1,4}" + r'(' + \
                  month_alphabetic + r'|' + months_numeric + r')' + not_alpha_numeric + r"{1,2}" + year

    # Initialize variables that will hold the found start and end date values (months and years)
    start_month = -1
    start_year = -1
    end_month = -1
    end_year = -1
    resume_text = ""
    duration_found = False

    def __init__(self, resume_text):
        self.resume_text = resume_text

    def find_number_of_durations(self):
        """Finds the number of durations in the resume, by searching for YYYY occurences,
        that is NOT followed by any digit for the next 10 characters."""
        # 01.2012 - 03.2014 will be counted once, as only the "2014" is picked up by the regex.
        # Good approximation for counting the total number of durations in the text.
        general_year_finder = r'\d{4}((?=[^\d]{10})|$)'
        regular_expression = re.compile(general_year_finder, re.IGNORECASE)
        regex_result = re.findall(regular_expression, self.resume_text)
        return len(regex_result)

    def calculate_experience_duration(self):
        """Calculates the date range in resume_text"""
        # Clean resume text for date recognition
        self.replace_to_with_hyphen_in_resume_text()
        self.resume_text = clean_text(self.resume_text)

        # Recognize durations of various formats
        self.find_full_date_range_numeric()
        self.find_full_date_range_alphabetic()
        self.find_month_and_year_range()
        self.find_month_ranges()
        self.find_unclosed_date_expression()
        self.standardize_month_number()
        return {
            'start_year': self.start_year,
            'end_year': self.end_year,
            'start_month': self.start_month,
            'end_month': self.end_month
        }

    def reset_found_dates(self):
        """Resets the found date members of the class."""
        self.start_month = -1
        self.start_year = -1
        self.end_year = -1
        self.end_month = -1

    def find_year_range(self):
        """"Finds a year range such as 2012 - 2013 or 2013 - 2014 - 2015"""
        regular_expression = re.compile(self.multi_year_range, re.IGNORECASE)
        regex_result = re.search(regular_expression, self.resume_text)

        if regex_result and not self.duration_found:
            self.reset_found_dates()
            duration = regex_result.group()

            self.find_start_year(duration)
            self.find_end_year_in_multirange(duration)

            self.start_month = '0' + str(1)
            self.end_month = '0' + str(1)

            self.duration_found = True
            # print(str(self.start_month) + "/" + str(self.start_year) + " - " + str(self.end_month) + "/" + str(
            #     self.end_year))

    def find_full_date_range_numeric(self):
        """Finds full date ranges in long version with day e.g.:( 01/01/2012-01/03/2014)"""
        regular_expression = re.compile(self.date_range_long_numeric, re.IGNORECASE)
        regex_result = re.search(regular_expression, self.resume_text)

        if regex_result and not self.duration_found:
            self.reset_found_dates()
            duration = regex_result.group()

            self.find_start_date(duration, self.month_numeric_long)
            self.find_end_date(duration,  self.month_numeric_long)

            self.duration_found = True

    def find_full_date_range_alphabetic(self):
        """Finds full date ranges in long version with day e.g.:(21 Jun, 2010 to 11 Sep, 2012)"""
        regular_expression = re.compile(self.date_range_alphabetic_long, re.IGNORECASE)
        regex_result = re.search(regular_expression, self.resume_text)

        if regex_result and not self.duration_found:
            self.reset_found_dates()
            duration = regex_result.group()

            self.find_start_date_with_alphabetic(duration, self.months_short, self.months_numeric)
            self.find_end_date_with_alphabetic(duration, self.months_short, self.months_numeric)

            self.duration_found = True
            # print(str(self.start_month) + "/" + str(self.start_year) + " - " + str(self.end_month) + "/" + str(self.end_year))

    def find_month_and_year_range(self):
        """Finds month and year ranges in both numeric and alphabetic ways
        04/2017 - 01/2018 || mar/2018 - jun/2019 || july/2015 - may/2016"""
        regular_expression = re.compile(self.date_range, re.IGNORECASE)
        regex_result = re.search(regular_expression, self.resume_text)
        if regex_result and not self.duration_found:
            self.reset_found_dates()
            duration = regex_result.group()

            self.find_start_date_with_alphabetic(duration, self.months_short, self.months_numeric)
            self.find_end_date_with_alphabetic(duration, self.months_short, self.months_numeric)
            self.duration_found = True
            # print(str(self.start_month) + "/" + str(self.start_year) + " - " + str(self.end_month) + "/" + str(self.end_year))

    def find_month_ranges(self):
        """Find month ranges such as 04-05. 2017"""
        regular_expression = re.compile(self.month_range, re.IGNORECASE)
        regex_result = re.search(regular_expression, self.resume_text)
        if regex_result and not self.duration_found:
            duration = regex_result.group()
            self.find_start_date_with_alphabetic(duration, self.months_short, self.months_numeric)

            # Find end month (start searching from start month)
            start_month_result = self.find_start_month_alphabetic(self.months_short, duration)
            if not start_month_result:
                start_month_result = self.find_start_month(self.months_numeric, duration)
            month_regex = re.compile(self.months_short, re.IGNORECASE)
            month_result = re.search(month_regex, duration[start_month_result.end():])
            if month_result:
                current_month = self.get_month_index(month_result.group())
                self.end_month = current_month
            else:
                month_regex = re.compile(self.months_numeric, re.IGNORECASE)
                month_result = re.search(month_regex, duration[start_month_result.end():])
                if month_result:
                    current_month = month_result.group()
                    self.end_month = int(current_month)
            self.end_year = self.start_year
            # print(str(self.start_month) + "/" + str(self.start_year) + " - " + str(self.end_month) + "/" + str(
            #     self.end_year))
            self.duration_found = True

    def find_unclosed_date_expression(self):
        """Finds date expressions, where the end-date was not specified at all."""
        start_only_regular_expression = re.compile(self.start_date_only, re.IGNORECASE)
        start_only_regex_result = re.search(start_only_regular_expression, self.resume_text)
        if start_only_regex_result and not self.duration_found:
            duration = start_only_regex_result.group()
            self.find_start_date_with_alphabetic(duration, self.months_short, self.months_numeric)
            # print(str(self.start_month) + '/' + str(self.start_year))
            self.duration_found = True

    def replace_to_with_hyphen_in_resume_text(self):
        """Replaces occurrences of "to" and "until" with "-". This is useful when the candidate describes the duration as
        01/2014 to 02/2015."""
        self.resume_text = self.resume_text.replace(" to ", " - ")
        self.resume_text = self.resume_text.replace(" until ", " - ")

    def find_start_date(self, duration, month_regex_type):
        """Extracts the start date from a given duration. E.g.: 04.2012 from 04.2012-05.2013"""
        if self.find_start_year(duration):
            self.find_start_month(month_regex_type, duration)

    def find_start_date_with_alphabetic(self, duration, month_regex_alphabetic, month_regex_numeric):
        """Extracts the alphanumeric start date from a duration."""
        if self.find_start_year(duration):
            if not self.find_start_month_alphabetic(month_regex_alphabetic, duration):
                self.find_start_month(month_regex_numeric, duration)

    def find_start_year(self, duration):
        """Extracts the start year from a duration"""
        year_regex = re.compile(self.year)
        year_result = re.search(year_regex, duration)
        if year_result:
            self.start_year = int(year_result.group())
        return year_result

    def find_start_month(self, month_regex_expression, duration):
        """Extracts the start month from a duration"""
        month_regex = re.compile(month_regex_expression, re.IGNORECASE)
        month_result = re.search(month_regex, duration)
        if month_result:
            current_month = month_result.group()
            self.start_month = int(current_month)
        return month_result

    def find_start_month_alphabetic(self, month_regex_expression, duration):
        """Extracts the alphabetic start month from a duration"""
        month_regex = re.compile(month_regex_expression, re.IGNORECASE)
        month_result = re.search(month_regex, duration)
        if month_result:
            current_month = self.get_month_index(month_result.group())
            self.start_month = int(current_month)
        return month_result

    def find_end_date(self, duration, month_regex_expression):
        """Finds the end date in the given duration"""
        if self.find_end_year(duration):
            self.find_end_month(month_regex_expression, duration)

    def find_end_date_with_alphabetic(self, duration, month_regex_alphabetic, month_regex_numeric):
        """Finds the end date in the given duration"""
        if self.find_end_year(duration):
            if not self.find_end_month_alphabetic(month_regex_alphabetic, duration):
                self.find_end_month(month_regex_numeric, duration)

    def is_end_date_now(self, duration):
        """Returns true if the duration contains 'present', 'now', 'today', or '...'"""
        return duration.lower().find('present') != -1 or duration.lower().find(
                'now') != -1 or duration.lower().find('today') != -1 or duration.lower().find('...') != -1

    def find_end_year(self, duration):
        """Extracts the end year from a given duration"""
        start_year = self.find_start_year(duration)
        end_year_result = re.search(self.year, duration[start_year.end():])
        if end_year_result:
            self.end_year = int(end_year_result.group())
        return end_year_result

    def find_end_year_in_multirange(self, duration):
        """Extracts the end year in a multi-year duration. Eg.: extracts 2015 from 2012 - 2013 - 2014"""
        year_regex = re.compile(self.year + r'$')
        end_year_result = re.search(year_regex, duration)
        if end_year_result:
            self.end_year = int(end_year_result.group())
        return end_year_result

    def find_end_month(self, month_regex_expression, duration):
        """Extracts the end-month from a duration"""
        start_year = self.find_start_year(duration)
        month_regex = re.compile(month_regex_expression, re.IGNORECASE)
        month_result = re.search(month_regex, duration[start_year.end():])
        if month_result:
            current_month = month_result.group()
            self.end_month = int(current_month)
        return month_result

    def find_end_month_alphabetic(self, month_regex_expression, duration):
        """Extracts the alphabetic end month from a duration"""
        start_year = self.find_start_year(duration)
        month_regex = re.compile(month_regex_expression, re.IGNORECASE)
        month_result = re.search(month_regex, duration[start_year.end():])
        if month_result:
            current_month = self.get_month_index(month_result.group())
            self.end_month = int(current_month)
        return month_result

    def standardize_month_number(self):
        """Feeds a leading zero to the month if it was not written with double digits.
        E.g.: (february) 2 -> 02, (may) 5 -> 05"""
        if len(str(self.start_month)) < 2:
            self.start_month = '0' + str(self.start_month)

        if len(str(self.end_month)) < 2:
            self.end_month = '0' + str(self.end_month)

    def get_month_index(self, month):
        """Returns the numeric representation of an alphabetic month"""
        month_dict = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9,
                      'oct': 10, 'nov': 11, 'dec': 12}
        return month_dict[month.lower()]