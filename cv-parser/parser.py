from pkg_resources import resource_string, resource_listdir
import json
from os import path
from collections import defaultdict

from .scraper import *
from .textCleaners import *
from .dateregex import *

from string import punctuation
from nltk.corpus import stopwords


def extract_information_into_json(html_path):
    """Parses the resume (of html format), extracts the relevant information, and returns it in a dictionary."""

    # Load section separator keywords (education, work experience, skills etc.) and their synonymes.
    section_separator_keywords_dict = load_section_separator_keywords_from_dictionary()

    # Load the external HTML resume to the memory using an internal representation (dictionary).
    resume_object = convert_html_resume_to_object(html_path)

    # Find sections in the resume using section separator keywords.
    parsed_resume = break_text_into_sections(resume_object, section_separator_keywords_dict)

    # Find the individual expereinces in the work experience section and find out their durations and used skills.
    parsed_resume = parse_work_experience(resume_object, parsed_resume)

    # Use a "learning algorithm" to identify yet unknown skills in the skills section
    learn_skills_from_resume(parsed_resume)

    # analyze the skill section for known skills / programming languages
    parsed_resume = parse_skills(parsed_resume)

    # Return the results as a json data.
    json_data = json.dumps(parsed_resume)
    return json_data


def load_section_separator_keywords_from_dictionary():
    """Loads the section keywords (e.g.: "Work Experience", "Skills") from the resources into a dictionary.
    The key is always the filename (E.g.: Skills.txt -> Skills) and the values are the list of keywords (skill, skills,
    abilities, languages etc."""

    keywords_dict = {}
    for name in resource_listdir('resources.keywordlists', ''):
        if os.path.splitext(name)[1] == '.txt':
            keywords_dict[os.path.splitext(name)[0]] = \
                resource_string('resources.keywordlists', name).decode("utf-8", "strict").splitlines()
    return keywords_dict


def break_text_into_sections(resume_info, keywords_dict):
    """Breaks the resume into sections and returns a dictionary that contains section keywords (work experience,
    skills etc.) as keys and the lines that correspond to the key as list of values."""

    visual_properties_of_resume = get_visual_properties_of_section_keywords(resume_info, keywords_dict)

    visual_properties_of_keywords_in_resume = deduce_visual_properties_of_keywords_in_resume(
        visual_properties_of_resume)

    return break_resume_in_sections(resume_info, keywords_dict, visual_properties_of_keywords_in_resume)


def get_visual_properties_of_section_keywords(resume_object, keywords_dict):
    """Section keywords are typically written with different style. (Capitals, bold (font-family), font-size,
    left margin, font-color etc.) This function extracts the visual properties of the section keywords found in
    the resume and returns these as a dictionary."""

    # Collect occurrences of visual properties.
    # E.g. for font-size: 46px : ["Education", "Work"], 42px : ["Skills", "Summary"] ...
    font_size_dict = defaultdict(list)
    font_family_dict = defaultdict(list)
    left_margin_dict = defaultdict(list)
    font_color_dict = defaultdict(list)

    # Store the number of occurrences of different visual properties. (e.g.: font_size : {'48px': 8, '44.16px': 1})
    # Properties of lines, where the entire line was written with capitals:
    all_caps_properties = {
        'font_size': {},
        'font_family': {},
        'left_margin': {},
        'font_color': {},
        'number_of_capital_matches': 0
    }
    # Properties of texts, where the line entirely matched the section keyword
    entire_match_properties = {
        'font_size': {},
        'font_family': {},
        'left_margin': {},
        'font_color': {},
    }

    for line in resume_object:
        line_text = clean_text_from_nonbasic_characters(line['line_text'])
        # key = Skills, values = [Abilities, Areas of Experience, Areas of Expertise, Areas of Knowledge]
        for key, value_list in keywords_dict.items():
            # Sort the values by their length in descending order. This is important otherwise "Experience" will be
            # matched before than "Work Experience" or "Areas of Experience" and these are more concrete / specific.
            value_list = sorted(value_list, key=len, reverse=True)
            for keyword in value_list:
                if keyword_found_in_text(keyword, line_text):
                    font_size_dict[line['font_size']].append(line_text)
                    font_family_dict[line['font_family']].append(line_text)
                    left_margin_dict[line['left_margin']].append(line_text)
                    font_color_dict[line['font_color']].append(line_text)

                    # If keywords are written with capitals, collect their visual properties.
                    if keyword_found_in_text_with_capitals(keyword, line_text):
                        all_caps_properties = add_line_props_to_dict(line, all_caps_properties)
                        all_caps_properties['number_of_capital_matches'] += 1

                    # If currnet line fully matches the keyword, collect their visual properties.
                    if keyword_fully_matches_text(keyword, line_text):
                        entire_match_properties = add_line_props_to_dict(line, entire_match_properties)
                    break

    return {
        'font_size_dict': font_size_dict,
        'font_family_dict': font_family_dict,
        'left_margin_dict': left_margin_dict,
        'font_color_dict': font_color_dict,
        'all_caps_properties': all_caps_properties,
        'entire_match_properties': entire_match_properties,
        'number_of_capital_matches': all_caps_properties['number_of_capital_matches']
    }


def keyword_found_in_text(keyword, line_text):
    """Returns true if the given keyword is matched anywhere in the text."""
    if (re.search(keyword, line_text, re.IGNORECASE)) is not None:
        return True
    return False


def keyword_found_in_text_with_capitals(keyword, line_text):
    """Returns true if the given keyword's capitalized version is matched anywhere in the text"""
    if (re.search(keyword.upper(), line_text)) is not None:
        return True
    return False


def keyword_fully_matches_text(keyword, line_text):
    """Returns true, if the text only contains the keyword and it matches the current keyword"""

    # Remove any non-number / non-letter characters and strip off additional start/end white-spaces
    line_text = replace_any_non_letter_or_number_character(line_text)
    if re.fullmatch(keyword.upper(), line_text.upper()) is not None:
        return True
    return False


def add_line_props_to_dict(line, visual_properties_dict):
    """Extracts the visual properties of the line and adds it to the dictionary.
    Returns the dictionary where the values have been "updated" with the current line's values."""

    if line['font_size'] not in visual_properties_dict['font_size'].keys():
        visual_properties_dict['font_size'][line['font_size']] = 1
    else:
        visual_properties_dict['font_size'][line['font_size']] += 1

    if line['font_color'] not in visual_properties_dict['font_color'].keys():
        visual_properties_dict['font_color'][line['font_color']] = 1
    else:
        visual_properties_dict['font_color'][line['font_color']] += 1

    if line['left_margin'] not in visual_properties_dict['left_margin'].keys():
        visual_properties_dict['left_margin'][line['left_margin']] = 1
    else:
        visual_properties_dict['left_margin'][line['left_margin']] += 1

    if line['font_family'] not in visual_properties_dict['font_family'].keys():
        visual_properties_dict['font_family'][line['font_family']] = 1
    else:
        visual_properties_dict['font_family'][line['font_family']] += 1

    return visual_properties_dict


def deduce_visual_properties_of_keywords_in_resume(visual_properties_of_resume):
    """Based on the visual properties of section keywords gathered earlier, deduces the properties (font-size,
    font-color etc.) that is common for section keywords. If the number of capital matches were at least 3 it is
    assumed that all section keywords were written with capitals."""

    properties_of_keywords_in_resume = {}
    properties_of_keywords_in_resume = deduce_font_color(properties_of_keywords_in_resume,
                                                         visual_properties_of_resume)
    properties_of_keywords_in_resume = deduce_font_family(properties_of_keywords_in_resume,
                                                          visual_properties_of_resume)
    properties_of_keywords_in_resume = deduce_font_size(properties_of_keywords_in_resume,
                                                        visual_properties_of_resume)
    properties_of_keywords_in_resume = deduce_left_margin(properties_of_keywords_in_resume,
                                                          visual_properties_of_resume)

    # If at least three section keywords were written with capital, we guess, that all of them are with capitals.
    if visual_properties_of_resume['number_of_capital_matches'] > 2:
        properties_of_keywords_in_resume['section_keywords_written_in_capital'] = True
    else:
        properties_of_keywords_in_resume['section_keywords_written_in_capital'] = False

    return properties_of_keywords_in_resume


def deduce_font_color(properties_of_keywords_in_resume, structural_properties_of_resume):
    """Takes the font-color that has at least 3 occurrences in all_caps_properties and
    entire_match_properties. If the font-colors match it returns the font-color immediately. If not,
    it returns the font-color with the more occurrences."""

    all_caps_properties = {}
    entire_match_properties = {}

    # key = colors, value = frequency of color in section keywords
    if bool(structural_properties_of_resume['all_caps_properties']['font_color']):
        # sort keys (colors) in descending order of the occurrences
        sorted_colors_by_occurrence = sorted(structural_properties_of_resume['all_caps_properties']['font_color'],
                                             key=lambda k:
                                             structural_properties_of_resume['all_caps_properties']['font_color'][k],
                                             reverse=True)
        for color in sorted_colors_by_occurrence:
            if structural_properties_of_resume['all_caps_properties']['font_color'][color] > 2:
                all_caps_properties[color] = \
                    structural_properties_of_resume['all_caps_properties']['font_color'][
                        color]
                break

    if bool(structural_properties_of_resume['entire_match_properties']['font_color']):
        sorted_colors_by_occurrence = sorted(structural_properties_of_resume['entire_match_properties']['font_color'],
                                             key=lambda k:
                                             structural_properties_of_resume['entire_match_properties']['font_color'][
                                                 k],
                                             reverse=True)
        for color in sorted_colors_by_occurrence:
            if structural_properties_of_resume['entire_match_properties']['font_color'][color] > 2:
                entire_match_properties[color] = \
                    structural_properties_of_resume['entire_match_properties']['font_color'][
                        color]
                break

    if bool(all_caps_properties) and bool(entire_match_properties):
        all_caps_color, all_caps_occurrence = all_caps_properties.popitem()
        entire_match_color, entire_match_occurrence = entire_match_properties.popitem()
        if all_caps_color == entire_match_color:
            properties_of_keywords_in_resume['font_color'] = all_caps_color
            return properties_of_keywords_in_resume
        if all_caps_occurrence > entire_match_occurrence:
            properties_of_keywords_in_resume['font_color'] = all_caps_color
            return properties_of_keywords_in_resume
        else:
            properties_of_keywords_in_resume['font_color'] = entire_match_color
            return properties_of_keywords_in_resume

    # If only one of all_caps_properties / entire_match_properties exist --> take that.
    if bool(all_caps_properties):
        all_caps_color, all_caps_occurrence = all_caps_properties.popitem()
        properties_of_keywords_in_resume['font_color'] = all_caps_color
        return properties_of_keywords_in_resume

    if bool(entire_match_properties):
        entire_match_color, entire_match_occurrence = entire_match_properties.popitem()
        properties_of_keywords_in_resume['font_color'] = entire_match_color
        return properties_of_keywords_in_resume

    return properties_of_keywords_in_resume


def deduce_font_size(properties_of_keywords_in_resume, structural_properties_of_resume):
    """Takes the largest font size that has more than 2 occurrences in all_caps_properties and
    entire_match_properties. If the font-size matches it returns the font-size immediately. If not,
    it returns the font-size with the more occurrences."""

    all_caps_properties = {}
    entire_match_properties = {}

    if bool(structural_properties_of_resume['all_caps_properties']['font_size']):
        keys = structural_properties_of_resume['all_caps_properties']['font_size'].keys()
        sorted_float_keys = sorted([float(key[:-2]) for key in keys], reverse=True)
        for float_key in sorted_float_keys:
            string_key = str(float_key)
            if string_key.endswith(".0"):
                string_key = string_key[:-2]
            if structural_properties_of_resume['all_caps_properties']['font_size'][string_key + "px"] > 2:
                all_caps_properties[string_key + "px"] = \
                    structural_properties_of_resume['all_caps_properties']['font_size'][
                        string_key + "px"]
                break

    if bool(structural_properties_of_resume['entire_match_properties']['font_size']):
        keys = structural_properties_of_resume['entire_match_properties']['font_size'].keys()
        sorted_float_keys = sorted([float(key[:-2]) for key in keys], reverse=True)
        for float_key in sorted_float_keys:
            string_key = str(float_key)
            if string_key.endswith(".0"):
                string_key = string_key[:-2]
            if structural_properties_of_resume['entire_match_properties']['font_size'][string_key + "px"] > 2:
                entire_match_properties[string_key + "px"] = \
                    structural_properties_of_resume['entire_match_properties']['font_size'][
                        string_key + "px"]
                break

    if bool(all_caps_properties) and bool(entire_match_properties):
        key_all, value_all = all_caps_properties.popitem()
        key_entire, value_entire = entire_match_properties.popitem()
        if key_all == key_entire:
            properties_of_keywords_in_resume['font_size'] = key_all
            return properties_of_keywords_in_resume
        if value_all > value_entire:
            properties_of_keywords_in_resume['font_size'] = key_all
            return properties_of_keywords_in_resume
        else:
            properties_of_keywords_in_resume['font_size'] = key_entire
            return properties_of_keywords_in_resume

    if bool(all_caps_properties):
        key_all, value_all = all_caps_properties.popitem()
        properties_of_keywords_in_resume['font_size'] = key_all
        return properties_of_keywords_in_resume

    if bool(entire_match_properties):
        key_entire, value_entire = entire_match_properties.popitem()
        properties_of_keywords_in_resume['font_size'] = key_entire
        return properties_of_keywords_in_resume

    return properties_of_keywords_in_resume


def deduce_left_margin(properties_of_keywords_in_resume, structural_properties_of_resume):
    """Takes the smallest left margin that has more than 2 occurrences in all_caps_properties and
    entire_match_properties. If both left_margin matched it returns the left_margin immediately. If not,
    it returns the left_margin with the more occurrences."""

    all_caps_properties = {}
    entire_match_properties = {}

    if bool(structural_properties_of_resume['all_caps_properties']['left_margin']):
        keys = structural_properties_of_resume['all_caps_properties']['left_margin'].keys()
        sorted_float_keys = sorted([float(key[:-2]) for key in keys], reverse=False)
        for float_key in sorted_float_keys:
            string_key = str(float_key)
            if string_key.endswith(".0"):
                string_key = string_key[:-2]
            if structural_properties_of_resume['all_caps_properties']['left_margin'][string_key + "px"] > 2:
                all_caps_properties[string_key + "px"] = \
                    structural_properties_of_resume['all_caps_properties']['left_margin'][
                        string_key + "px"]
                break

    if bool(structural_properties_of_resume['entire_match_properties']['left_margin']):
        keys = structural_properties_of_resume['entire_match_properties']['left_margin'].keys()
        sorted_float_keys = sorted([float(key[:-2]) for key in keys], reverse=False)
        for float_key in sorted_float_keys:
            string_key = str(float_key)
            if string_key.endswith(".0"):
                string_key = string_key[:-2]
            if structural_properties_of_resume['entire_match_properties']['left_margin'][string_key + "px"] > 2:
                entire_match_properties[string_key + "px"] = \
                    structural_properties_of_resume['entire_match_properties']['left_margin'][
                        string_key + "px"]
                break

    if bool(all_caps_properties) and bool(entire_match_properties):
        key_all, value_all = all_caps_properties.popitem()
        key_entire, value_entire = entire_match_properties.popitem()
        if key_all == key_entire:
            properties_of_keywords_in_resume['left_margin'] = key_all
            return properties_of_keywords_in_resume
        if value_all > value_entire:
            properties_of_keywords_in_resume['left_margin'] = key_all
            return properties_of_keywords_in_resume
        else:
            properties_of_keywords_in_resume['left_margin'] = key_entire
            return properties_of_keywords_in_resume

    if bool(all_caps_properties):
        key_all, value_all = all_caps_properties.popitem()
        properties_of_keywords_in_resume['left_margin'] = key_all
        return properties_of_keywords_in_resume

    if bool(entire_match_properties):
        key_entire, value_entire = entire_match_properties.popitem()
        properties_of_keywords_in_resume['left_margin'] = key_entire
        return properties_of_keywords_in_resume

    return properties_of_keywords_in_resume


def deduce_font_family(properties_of_keywords_in_resume, structural_properties_of_resume):
    """Takes the most used font family that has more than 2 occurrences in all_caps_properties and
        entire_match_properties. If both font families are the same it returns the font family immediately. If not,
        it returns the font family with the more occurrences."""

    all_caps_properties = {}
    entire_match_properties = {}

    if bool(structural_properties_of_resume['all_caps_properties']['font_family']):
        sorted_keys_by_value = sorted(structural_properties_of_resume['all_caps_properties']['font_family'],
                                      key=lambda k:
                                      structural_properties_of_resume['all_caps_properties']['font_family'][k],
                                      reverse=True)
        for key in sorted_keys_by_value:
            if structural_properties_of_resume['all_caps_properties']['font_family'][key] > 2:
                all_caps_properties[key] = \
                    structural_properties_of_resume['all_caps_properties']['font_family'][
                        key]
                break

    if bool(structural_properties_of_resume['entire_match_properties']['font_family']):
        sorted_keys_by_value = sorted(structural_properties_of_resume['entire_match_properties']['font_family'],
                                      key=lambda k:
                                      structural_properties_of_resume['entire_match_properties']['font_family'][k],
                                      reverse=True)
        for key in sorted_keys_by_value:
            if structural_properties_of_resume['entire_match_properties']['font_family'][key] > 2:
                entire_match_properties[key] = \
                    structural_properties_of_resume['entire_match_properties']['font_family'][
                        key]
                break

    if bool(all_caps_properties) and bool(entire_match_properties):
        key_all, value_all = all_caps_properties.popitem()
        key_entire, value_entire = entire_match_properties.popitem()
        if key_all == key_entire:
            properties_of_keywords_in_resume['font_family'] = key_all
            return properties_of_keywords_in_resume
        if value_all > value_entire:
            properties_of_keywords_in_resume['font_family'] = key_all
            return properties_of_keywords_in_resume
        else:
            properties_of_keywords_in_resume['font_family'] = key_entire
            return properties_of_keywords_in_resume

    if bool(all_caps_properties):
        key_all, value_all = all_caps_properties.popitem()
        properties_of_keywords_in_resume['font_family'] = key_all
        return properties_of_keywords_in_resume

    if bool(entire_match_properties):
        key_entire, value_entire = entire_match_properties.popitem()
        properties_of_keywords_in_resume['font_family'] = key_entire
        return properties_of_keywords_in_resume

    return properties_of_keywords_in_resume


def break_resume_in_sections(resume_info, keywords_dict, visual_properties_of_keywords_in_resume):
    """Breaks the resume into sections (Skills, WorkExpereince), using the visual properties of keywords."""
    result = defaultdict(list)
    if not is_amount_of_visual_properties_data_satisfactory(visual_properties_of_keywords_in_resume):
        print("Less then three visual properties were extracted for section keywords. "
              "Resume was not broken into sections.")
        return result

    # Lines that were not recognized as section keyword will be put under this section in the output.
    current_section_keyword = ""

    for line in resume_info:
        if line_has_visual_properties_of_section_keywords(line, visual_properties_of_keywords_in_resume):
            # Check if line matches any section keyword, and if so get the matched section keyword
            line_matches_section_keyword = False
            section_keyword_match_found = section_keyword_matched_in_line(line, keywords_dict, current_section_keyword)
            if current_section_keyword != section_keyword_match_found:
                current_section_keyword = section_keyword_match_found
                line_matches_section_keyword = True

            # If not matched, but section_keywords are with capital, and line is capital -> it is probably section keyword
            if not line_matches_section_keyword and line['line_text'].strip():
                if visual_properties_of_keywords_in_resume['section_keywords_written_in_capital']:
                    if is_text_all_capital(line["line_text"]) and not clean_text_from_nonbasic_characters(
                            line['line_text']):
                        current_section_keyword = line['line_text']
                    # If keywords are with capital, but this text is not, then simply append to current section's text
                    else:
                        result[current_section_keyword].append(line['line_text'])
                # Since line had visual properties of section keywords assume it is.
                else:
                    current_section_keyword = line['line_text']

        # If it's a normal line append it to the current section we are in.
        elif current_section_keyword and line['line_text'].strip():
            result[current_section_keyword].append(line['line_text'])
    return result


def is_amount_of_visual_properties_data_satisfactory(visual_properties_of_keywords_in_resume):
    """If we have at least 4 visual properties (including capital keywords) OR
    we have at least 3 AND we know that sections words are written with capitals return true."""
    visual_property_names = list(visual_properties_of_keywords_in_resume.keys())
    return len(visual_property_names) > 3 or \
           (len(visual_property_names) == 3
            and visual_properties_of_keywords_in_resume['section_keywords_written_in_capital'])


def line_has_visual_properties_of_section_keywords(line, visual_properties_of_keywords_in_resume):
    """Returns true if the line's given visual property is similar to the property of section keywords"""
    result = True
    for visual_property in visual_properties_of_keywords_in_resume.keys():
        if visual_property != "section_keywords_written_in_capital":
            if visual_properties_of_keywords_in_resume[visual_property] != line[visual_property]:
                result = False
                break
        else:
            if visual_properties_of_keywords_in_resume[visual_property]:
                if line['line_text'] != line['line_text'].upper():
                    result = False
                    break
    return result


def section_keyword_matched_in_line(line, keywords_dict, current_section_keyword):
    """Iterates over the section keyword dictionary and checks if the current line's text contains any of the
    section keywords. If so, it returns the found section keyword. If no matches found returns current_section_keyword"""
    for section_keyword_name, section_keyword_variations in keywords_dict.items():
        for section_keyword in section_keyword_variations:
            if (re.search(
                    section_keyword.upper(),
                    clean_text_from_nonbasic_characters(line['line_text']).upper())) is not None:
                return section_keyword_name
    return current_section_keyword


def is_text_all_capital(text):
    """Returns true of the entire text is written with capitals. False otherwise."""
    return text == text.upper()


def parse_work_experience(resume_object, parsed_resume):
    """Identify individual work experiences, find the duration of the job and look for skills in their text."""
    if 'WorkExperience' not in parsed_resume:
        return parsed_resume

    # Filter out empty lines and find the start and end index of the WE section in resume_object
    parsed_resume_no_empty_lines = [line for line in parsed_resume['WorkExperience'] if
                                    replace_newline_with_space(line).strip()]
    filtered_resume_info = [line for line in resume_object if replace_newline_with_space(line['line_text'].strip())]
    work_exp_indexes = find_workexperience_line_indexes_in_resume_object(parsed_resume_no_empty_lines,
                                                                         filtered_resume_info)

    # Create containers and append the first work expereince to our dictionary
    job_experiences = []
    job = {
        'description': [],
        'startDate': "",
        'endDate': "",
        "skills": []
    }

    job['description'].append(filtered_resume_info[work_exp_indexes["start_index"]]['line_text'])

    complete_resume_text = get_complete_work_experince_text(work_exp_indexes, filtered_resume_info)

    # Guess the number of experiences in the text, based on the found durations.
    numer_of_expected_work_experiences = find_number_of_dates_in_text(complete_resume_text)

    # Find end of section based on change in horizontal difference and left-margin difference
    find_section_based_on_horizontal_diff_and_leftmargin_diff(work_exp_indexes, filtered_resume_info,
                                                              job_experiences, job)

    # If we didn't find at least half of the experiences, find sections that were seperated by new lines.
    if len(job_experiences) <= numer_of_expected_work_experiences / 2:
        job_experiences_new = find_section_based_on_enter(resume_object, parsed_resume)
        if len(job_experiences_new) > len(job_experiences):
            job_experiences = job_experiences_new

    # If we didn't find at least half of the experiences, find sections based only on the horizontal difference between lines.
    if len(job_experiences) <= numer_of_expected_work_experiences / 2:
        job_experiences_new = find_section_based_on_horizontal_diff_only(resume_object, parsed_resume)
        if len(job_experiences_new) > len(job_experiences):
            job_experiences = job_experiences_new

    # If we didn't find at least half of the experiences, find sections based on left margin.
    if len(job_experiences) <= numer_of_expected_work_experiences / 2:
        job_experiences_new = find_section_based_on_left_margin_only(work_exp_indexes, filtered_resume_info)
        if len(job_experiences_new) > len(job_experiences):
            job_experiences = job_experiences_new
    job_experiences = find_dates_in_job(job_experiences)
    job_experiences = find_skills_in_job(job_experiences)
    parsed_resume['WorkExperience'] = job_experiences
    return parsed_resume


def find_workexperience_line_indexes_in_resume_object(parsed_resume_no_empty_lines, filtered_resume_info):
    """Finds the first and last indexes in resume_object, where the lines correspond to the work_experience.
    Returns the index if found, else None."""
    we_first_line_text = "" if not parsed_resume_no_empty_lines else parsed_resume_no_empty_lines[0]
    we_last_line_text = "" if not parsed_resume_no_empty_lines else parsed_resume_no_empty_lines[-1]

    first_line_index = 0
    last_line_index = 0
    if we_first_line_text and we_last_line_text:
        for i, line in enumerate(filtered_resume_info):
            if line['line_text'] == we_first_line_text:
                first_line_index = i
            if line['line_text'] == we_last_line_text:
                last_line_index = i
    return {'start_index': first_line_index, 'end_index': last_line_index}


def get_complete_work_experince_text(work_exp_indexes, filtered_resume_info):
    """Extract the text of a given work experience from the reusme, using the work_exp_indexes that
    determint the start and end line (index) in the filtered_resume_info"""
    text = ""
    for index in range(work_exp_indexes['start_index'] + 1, work_exp_indexes['end_index'] + 1):
        text += filtered_resume_info[index]['line_text'] + '\n'
    return text


def find_number_of_dates_in_text(text):
    """Finds the number of durations in the text. (01/2016-02/2016 counts as one.)"""
    dr = DateRegex(text)
    return dr.find_number_of_durations()


def find_section_based_on_horizontal_diff_and_leftmargin_diff(work_exp_indexes, filtered_resume_info,
                                                              job_experiences, job):
    """Default work experience sectioning strategy, where both horizontal and vertical spacing is used to determine,
    whether a new section is starting."""
    previous_horizontal_diffs = []

    if work_exp_indexes['start_index'] != 0 and work_exp_indexes['end_index'] != 0:
        for index in range(work_exp_indexes['start_index'] + 1, work_exp_indexes['end_index'] + 1):
            # New Section based on Horizontal change?
            horizontal_space_diff_between_current_and_last_line = \
                int(float(filtered_resume_info[index - 1]['bottom_margin'][:-2]) -
                    float(filtered_resume_info[index]['bottom_margin'][:-2]))
            pageChange = filtered_resume_info[index]['page_number'] != filtered_resume_info[index - 1][
                'page_number']

            new_section_based_on_change_in_horizontal_distance = \
                is_new_section_based_on_horizontal_difference(pageChange,
                                                              horizontal_space_diff_between_current_and_last_line,
                                                              previous_horizontal_diffs)
            previous_horizontal_diffs.append(abs(horizontal_space_diff_between_current_and_last_line))

            # New Section based on Left margin change?
            new_section_based_on_change_in_left_margin = False
            left_margin_diff_between_current_and_last_line = \
                int(float(filtered_resume_info[index - 1]['left_margin'][:-2]) -
                    float(filtered_resume_info[index]['left_margin'][:-2]))
            if left_margin_diff_between_current_and_last_line > 0:
                new_section_based_on_change_in_left_margin = True

            if new_section_based_on_change_in_horizontal_distance and new_section_based_on_change_in_left_margin:
                job_experiences.append(job)
                job = {
                    'description': [filtered_resume_info[index]['line_text']],
                    'startDate': "",
                    'endDate': "",
                    "skills": []
                }
            else:
                job['description'].append(filtered_resume_info[index]['line_text'])
        job_experiences.append(job)


def is_new_section_based_on_horizontal_difference(pageChange, horizontal_space_diff_between_current_and_last_line,
                                                  previous_horizontal_diffs):
    """
    Returns true, if based on pageChange and horizontal-diff a new section is starting.

    horizontal_space_diff is negative if:
        - We are on a new page
        - A new column started on the same page

    If delta_H is positive and it is greater than the previous delta_H with at least * TRESHOLD times, then new section
    """
    HORIZONTAL_DIFF_TRESHOLD = 1.4
    if not previous_horizontal_diffs: return False
    return pageChange or (horizontal_space_diff_between_current_and_last_line > 0 and
                          previous_horizontal_diffs and
                          horizontal_space_diff_between_current_and_last_line > (
                              previous_horizontal_diffs[-1] * HORIZONTAL_DIFF_TRESHOLD))


def find_section_based_on_enter(resume_object, parsed_resume):
    """A fallback work experience separation strategy, where blank lines are used to identify new sections."""
    parsed_resume_no_empty_lines = [line for line in parsed_resume['WorkExperience'] if
                                    replace_newline_with_space(line).strip()]
    work_exp_indexes = find_workexperience_line_indexes_in_resume_object(parsed_resume_no_empty_lines,
                                                                         resume_object)

    job_experiences = []
    job = {
        'description': [],
        'startDate': "",
        'endDate': "",
        "skills": []
    }
    job['description'].append(resume_object[work_exp_indexes["start_index"]]['line_text'])

    we_found = False
    if work_exp_indexes['start_index'] != 0 and work_exp_indexes['end_index'] != 0:
        for index in range(work_exp_indexes['start_index'] + 1, work_exp_indexes['end_index'] + 1):
            if not replace_newline_with_space(resume_object[index]['line_text']).strip():
                we_found = True
                job_experiences.append(job)
                job = {
                    'description': [],
                    'startDate': "",
                    'endDate': "",
                    "skills": []
                }
            else:
                job['description'].append(resume_object[index]['line_text'])
        if we_found:
            job_experiences.append(job)
    return job_experiences


def find_section_based_on_horizontal_diff_only(resume_object, parsed_resume):
    """A fallback work experience separation strategy, where only the horizontal difference
     is used to identify new sections."""
    parsed_resume_no_empty_lines = [line for line in parsed_resume['WorkExperience'] if
                                    replace_newline_with_space(line).strip()]
    work_exp_indexes = find_workexperience_line_indexes_in_resume_object(parsed_resume_no_empty_lines,
                                                                         resume_object)

    job_experiences = []
    job = {
        'description': [],
        'startDate': "",
        'endDate': "",
        "skills": []
    }
    job['description'].append(resume_object[work_exp_indexes["start_index"]]['line_text'])
    previous_horizontal_diffs = []

    we_found = False
    if work_exp_indexes['start_index'] != 0 and work_exp_indexes['end_index'] != 0:
        for index in range(work_exp_indexes['start_index'] + 1, work_exp_indexes['end_index'] + 1):
            # New Section based on Horizontal change?
            horizontal_space_diff_between_current_and_last_line = \
                int(float(resume_object[index - 1]['bottom_margin'][:-2]) -
                    float(resume_object[index]['bottom_margin'][:-2]))
            pageChange = resume_object[index]['page_number'] != resume_object[index - 1][
                'page_number']

            new_section_based_on_change_in_horizontal_distance = \
                is_new_section_based_on_horizontal_difference(pageChange,
                                                              horizontal_space_diff_between_current_and_last_line,
                                                              previous_horizontal_diffs)
            previous_horizontal_diffs.append(abs(horizontal_space_diff_between_current_and_last_line))

            if new_section_based_on_change_in_horizontal_distance:
                we_found = True
                job_experiences.append(job)
                job = {
                    'description': [resume_object[index]['line_text']],
                    'startDate': "",
                    'endDate': "",
                    "skills": []
                }
            else:
                job['description'].append(resume_object[index]['line_text'])
        if we_found:
            job_experiences.append(job)
    return job_experiences


def find_section_based_on_left_margin_only(work_exp_indexes, filtered_resume_info):
    """A fallback work experience separation strategy, where only the left margin is used to indentify new sections."""
    job_experiences = []
    job = {
        'description': [],
        'startDate': "",
        'endDate': "",
        "skills": []
    }
    job['description'].append(filtered_resume_info[work_exp_indexes["start_index"]]['line_text'])

    we_found = False
    if work_exp_indexes['start_index'] != 0 and work_exp_indexes['end_index'] != 0:
        for index in range(work_exp_indexes['start_index'] + 1, work_exp_indexes['end_index'] + 1):

            new_section_based_on_change_in_left_margin = False
            left_margin_diff_between_current_and_last_line = \
                int(float(filtered_resume_info[index - 1]['left_margin'][:-2]) -
                    float(filtered_resume_info[index]['left_margin'][:-2]))
            if left_margin_diff_between_current_and_last_line > 0:
                new_section_based_on_change_in_left_margin = True

            if new_section_based_on_change_in_left_margin:
                we_found = True
                job_experiences.append(job)
                job = {
                    'description': [filtered_resume_info[index]['line_text']],
                    'startDate': "",
                    'endDate': "",
                    "skills": []
                }
            else:
                job['description'].append(filtered_resume_info[index]['line_text'])
        if we_found:
            job_experiences.append(job)
    return job_experiences


def find_dates_in_job(job_experiences):
    """Finds the duration of each job experience and adds it to the given job's dictionary."""
    for job in job_experiences:
        job_text = get_full_job_description_text(job)
        dr = DateRegex(job_text)
        duration_dict = dr.calculate_experience_duration()

        job['startDate'] = ""
        job['endDate'] = ""
        if duration_dict['start_month'] != -1 and duration_dict['start_year'] != -1:
            job['startDate'] = '01.' + str(duration_dict['start_month']) + "." + str(duration_dict['start_year'])
        if duration_dict['end_month'] != -1 or duration_dict['end_year'] != -1:
            job['endDate'] = '01.' + str(duration_dict['end_month']) + "." + str(duration_dict['end_year'])
        if duration_dict['start_month'] == -1 and duration_dict['end_month'] == -1 and \
                        duration_dict['start_year'] != -1 and duration_dict['end_year'] != -1:
            job['startDate'] = '01.01.' + str(duration_dict['start_year'])
            job['endDate'] = '31.12.' + str(duration_dict['end_year'])
    return job_experiences


def get_full_job_description_text(job):
    """Returns the job_description as a continuous text, concatenated from the separate lines."""
    job_text = ""
    for line in job['description']:
        job_text += (line + " ")  # EOL " " to help date extraction
    return job_text.replace("  ", " ")


def find_skills_in_job(job_experiences):
    """Looks through each job experiences and analyzes its text for known skills."""
    for job in job_experiences:
        job_text = get_full_job_description_text(job)
        job_text = remove_end_of_sentence_punctuation(job_text)
        if "skills" in job:
            job["skills"] = find_skills_in_text(job_text.lower())
    return job_experiences


def find_skills_in_text(text):
    """Looks through the entire skill section, looking for skills."""
    skills = resource_string('resources.extracted-lists', "skills_to_find.txt").decode("utf-8",
                                                                                      "strict").splitlines()

    skills.sort(key=len, reverse=True)
    found_skills = []
    for skill in skills:
        match = re.search(r'((?<=^)|(?<=[^a-zA-Z\d]))' + re.escape(skill.lower()) + r'(?=$|[^a-zA-Z\d])', text.lower())
        if match:
            text = text.replace(match.group(), "")
            found_skills.append(skill)

    return found_skills


def find_skills_for_skill_learning(word, known_word_but_not_skill, found_skills_set):
    """Checks whether the given word is a skill, or not a skill."""
    skills = resource_string('resources.extracted-lists', "skills_to_find.txt").decode("utf-8",
                                                                                      "strict").splitlines()

    if word.lower() in known_word_but_not_skill:
        return False

    if word.lower() in skills:
        if found_skills_set is not None:
            found_skills_set.add(word.lower())
            return True
    known_word_but_not_skill.add(word.lower())
    return False


def parse_skills(resume_dict):
    """Creates 'SkillsRecognizedInSkillSection' that contains the list of the recognized skills and creates
     'SkillsCleaned' that contains the cleaned text of the skill section."""
    if "Skills" in resume_dict:
        skills_text = ""
        for line in resume_dict["Skills"]:
            skills_text += (line + " ")
        skills_text = clean_text_for_skill_extraction(skills_text).lower()
        skills_text = remove_end_of_sentence_punctuation(skills_text)
        resume_dict["SkillsRecognizedInSkillSection"] = find_skills_in_text(skills_text)
        resume_dict["SkillsCleaned"] = skills_text
    return resume_dict


def learn_skills_from_resume(resume_dict):
    """Checks each word of the skill section, whether it is a known skill. If there is an unknown word, between to
    known skill-words, then we can assume, that the word in the middle is also a skill, hence it is added to the skill
    dictionary."""

    skills_to_avoid = resource_string('resources.extracted-lists', "skills_to_avoid.txt").decode("utf-8",
                                                                                      "strict").splitlines()

    if "Skills" in resume_dict:
        skills_text = ""
        for line in resume_dict["Skills"]:
            skills_text += (line + " ")
        skills_text = clean_text_for_skill_extraction(skills_text).lower()
        skills_text = remove_end_of_sentence_punctuation(skills_text)
        skills_list = skills_text.split(' ')

        # Filter list from stopwords
        stop_words = stopwords.words('english') + list(punctuation)
        skills_list = [skill for skill in skills_list if skill not in stop_words]

        known_words = set()
        found_skills = set()
        if len(skills_list) >= 3:
            for x in range(1, len(skills_list) - 1):
                prev_is_skill = find_skills_for_skill_learning(skills_list[x - 1], known_words, found_skills)
                current_is_not_skill = not find_skills_for_skill_learning(skills_list[x], known_words, found_skills)
                next_is_skill = find_skills_for_skill_learning(skills_list[x + 1], known_words, found_skills)
                if prev_is_skill and current_is_not_skill and next_is_skill and skills_list[x].lower() not in skills_to_avoid:
                    file_path = path.relpath("resources/extracted-lists/skills_to_find.txt")
                    with open(file_path, "a") as myfile:
                        myfile.write("\n" + skills_list[x])

