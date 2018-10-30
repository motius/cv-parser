import re
from nltk.tokenize import sent_tokenize


# Module containing various text cleaning functions


def clean_text_from_geometrical_shape_unicode(line):
    """Cleans the line from geometrical shape characters and replaces these with space."""
    line = re.sub(r"([\u25A0-\u25FF])", " ", line)
    return line


def clean_text_from_private_unicode(line):
    """Cleans the line from private unicode characters and replaces these with space."""
    line = re.sub(r"([\uE000-\uF8FF]|\uD83C[\uDF00-\uDFFF]|\uD83D[\uDC00-\uDDFF])", " ", line)
    return line


def clean_text_from_latin_supplement_unicode(text):
    """Clears the text from latin supplement unicodes.
    https://apps.timwhitlock.info/unicode/inspect/hex/0080-00FF"""
    return re.sub(r"([\u0080-\u00FF])", " ", text)


def clean_text_from_general_punctuation_unicode(text):
    """Clears the text from general punctuation unicodes
    https://apps.timwhitlock.info/unicode/inspect/hex/2000-206F"""
    return re.sub(r"([\u2000-\u206F])", " ", text)


def clean_text_from_nonbasic_characters(text):
    """Clear the text from any characters that would prevent matching words with regex. These include
    special punctuations, bullet points, new lines etc."""
    text = re.sub(r"([^\u0000-\u007F])", " ", text)
    text = replace_newline_with_space(text).strip()
    text = text.replace("_", "")
    text = clean_text_from_multiple_consecutive_whitespaces(text)
    return text


def clean_text_from_multiple_consecutive_whitespaces(text):
    """Cleans the text from multiple consecutive whitespaces, by replacing these with a single whitespace."""
    multi_space_regex = re.compile(r"\s+", re.IGNORECASE)
    return re.sub(multi_space_regex, ' ', text)


def replace_newline_with_space(text):
    """Replaces new line with a space in text"""
    return re.sub("[\n\r]", " ", text)


def clean_text(text):
    """Cleans the text from brackets, punctuations, multiple white spaces and from +?*# signs."""
    text = text.replace("\uf0b7", " ")
    text = text.replace(":", " ")
    text = text.replace(".", " ")
    text = text.replace(",", " ")
    text = text.replace("/", " ")
    text = text.replace("(", " ")
    text = text.replace(")", " ")
    text = text.replace("[", " ")
    text = text.replace("]", " ")
    text = text.replace("+", " ")
    text = text.replace("?", " ")
    text = text.replace("*", " ")
    text = text.replace("#", " ")

    text = clean_text_from_multiple_consecutive_whitespaces(text)

    text = re.sub(" $", "", text)
    return text


def clean_text_for_skill_extraction(text):
    """Cleans the text for skill extraction by removing ambiguous
    characters as well as punctuations and brackets. """
    multi_space_regex = re.compile(r"[,;?!()\\/]", re.IGNORECASE)
    text = re.sub(multi_space_regex, ' ', text)

    text = clean_text_from_private_unicode(text)
    text = clean_text_from_geometrical_shape_unicode(text)

    text = clean_text_from_multiple_consecutive_whitespaces(text)

    return text


def remove_end_of_sentence_punctuation(text):
    """Removes end of sentence punctuation by replacing these with a space."""
    # Remove end of sentence dot
    new_text = ""
    sentences = sent_tokenize(text)
    for sentence in sentences:
        if sentence[-1] == '.':
            new_text += sentence[:-1] + " "
        else:
            new_text += sentence
    return new_text


def replace_any_non_letter_or_number_character(text):
    """Removes any non alphanumeric character"""
    text = text.strip()
    text = re.sub('[^A-Za-z0-9 ]+', '', text)
    return text


def escape_special_characters_for_regex(expression):
    """Escapes special characters used in a regex. For example if the regex contains '#'
    (from the skill C# for example), it needs to be escaped by a backslash to build a valid regex."""
    spec_char_escaper = re.compile(r"[^a-zA-Z0-9]", re.IGNORECASE)
    expression = re.sub(spec_char_escaper, r'\1', expression)
    return expression


def clean_for_comparison(text):
    """Cleans the text by removing almost all non-alphanumeric characters."""
    text = clean_text(text)
    text = clean_text_from_nonbasic_characters(text)
    return text