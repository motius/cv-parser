import argparse
import sys

from main.parser import *


def create_arg_parser():
    """"Creates and returns the ArgumentParser object."""

    parser = argparse.ArgumentParser(description='Extract skills and work experience from IT-resumes.')
    parser.add_argument('inputDirectory',
                        help='Path to the directory that contains the resumes.')
    parser.add_argument('--targetDirectory',
                        help='Path to the target directory that will contain the output.')
    return parser


def passed_arguments_are_correct(parsed_args):
    """Checks if the passed arguments are valid directories. Returns true if they are, false if not."""

    if not os.path.isdir(parsed_args.inputDirectory):
        print('Argument passed for inputDirectory is not valid. Please provide a valid directory!')
        return False
    if parsed_args.targetDirectory is not None:
        if not os.path.isdir(parsed_args.targetDirectory):
            print('Argument passed for targetDirectory is not valid. Please provide a valid directory!')
            return False
    return True


def start_resume_parsing(parsed_args):
    """Starts the resume parsing for each file found in the input directory"""

    print('Parsing resumes in dir:', parsed_args.inputDirectory)

    for root, dirs, files in os.walk(parsed_args.inputDirectory):
        if files.__len__() == 0:
            print("The directory doesn't contain any files!")
            return

        for filename in files:
            if filename.endswith(".pdf") or filename.endswith(".PDF"):
                file_path = os.path.join(root, filename)
                parse_resume(file_path, parsed_args.targetDirectory)


def parse_resume(resume_path, target_dir):
    """Parses the resume provided in resume_path and puts the output in target_dir"""

    renamed_resume_path = remove_blanks_from_filename(resume_path)
    os.rename(resume_path, renamed_resume_path)

    print("Processing: " + renamed_resume_path)
    html_resume_path = convert_pdf_to_html(renamed_resume_path)
    if html_resume_path is not None:
        json_data = extract_information_into_json(html_resume_path)
        filename = os.path.split(renamed_resume_path)[1]
        if target_dir is None:
            target_dir = os.path.split(renamed_resume_path)[0]
        output_path = os.path.join(target_dir, os.path.splitext(filename)[0] + ".json")
        with open(output_path, 'w') as outfile:
            outfile.write(json_data + '\n')


def remove_blanks_from_filename(file_path):
    new_name = file_path.replace(" ", "_")
    return new_name


if __name__ == "__main__":
    arg_parser = create_arg_parser()
    parsed_args = arg_parser.parse_args(sys.argv[1:])

    if passed_arguments_are_correct(parsed_args):
        start_resume_parsing(parsed_args)
