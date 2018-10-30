from __future__ import division
import os
import json
from datetime import datetime

from textCleaners import *


def start():
    """Compares the "ground trugh" jsons against the exported jsons"""

    ground_truth_path = "/home/phoenix/Desktop/Comparison/gt"
    export_path = "/home/phoenix/Desktop/Comparison/out"

    accuracy = {
        "startDate_truePositive": 0,
        "startDate_falsePositive": 0,
        "startDate_falseNegative": 0,
        "endDate_truePositive": 0,
        "endDate_falsePositive": 0,
        "endDate_falseNegative": 0,
        "description_truePositive": 0,
        "description_falsePositive": 0,
        "description_falseNegative": 0,
        "skilltext_truePositive": 0,
        "skilltext_falsePositive": 0,
        "skilltext_falseNegative": 0,
        "skillextracted_truePositive": 0,
        "skillextracted_falsePositive": 0,
        "skillextracted_falseNegative": 0,
        "totalResumes": 0
    }

    for root, dirs, files in os.walk(ground_truth_path):
        if files.__len__() == 0:
            print("The directory doesn't contain any files!")
            return
        for filename in files:
            if os.path.splitext(filename)[1] == '.json':
                ground_truth_file_path = os.path.join(root, filename)
                corresponding_export_path = os.path.join(export_path, filename)
                if os.path.isfile(corresponding_export_path):
                    json_groundtruth = load_json_from_file(ground_truth_file_path)
                    json_corresponding_export = load_json_from_file(corresponding_export_path)
                    compare_work_expereinces(json_groundtruth, json_corresponding_export, accuracy)
                    compare_skills(json_groundtruth, json_corresponding_export, accuracy)
    return accuracy


def load_json_from_file(path):
    with open(path) as json_data:
        d = json.load(json_data)
        json_data.close()
        return d


def compare_work_expereinces(json_truth, json_export, accuracy):
    if "work" not in json_truth or "WorkExperience" not in json_export:
        return accuracy

    list_of_truth_experiences = json_truth["work"]
    list_of_export_experiences = json_export["WorkExperience"]

    # If there are no work experiences in the truth:
    if len(list_of_truth_experiences) == 0 or not bool(list_of_truth_experiences[0]):
        return accuracy

    # Number of work experiences in ground-truth resume.
    accuracy["totalResumes"] += len(list_of_truth_experiences)

    for truth_experience in list_of_truth_experiences:
        truth_startDate = ""
        truth_endDate = ""
        truth_description = ""
        if "startDate" in truth_experience:
            if truth_experience["startDate"] != "":
                truth_startDate = datetime.strptime(truth_experience["startDate"], "%d.%m.%Y").strftime('%d.%m.%Y')
        if "endDate" in truth_experience:
            if truth_experience["endDate"] != "":
                truth_endDate = datetime.strptime(truth_experience["endDate"], "%d.%m.%Y").strftime('%d.%m.%Y')
        if "summary" in truth_experience:
            truth_description = truth_experience["summary"]

        corresponsing_experience_found = False

        # Find the corresponding expereince in the exported one
        for expereince in list_of_export_experiences:
            startDate = ""
            endDate = ""
            description = ""
            if "startDate" in expereince:
                startDate = expereince["startDate"]
            if "endDate" in expereince:
                endDate = expereince["endDate"]
            if "description" in expereince:
                description = expereince["description"]

            # Find matching workExperiences based on text
            if match_descriptions(truth_description, description):

                accuracy["description_truePositive"] += 1
                corresponsing_experience_found = True

                # If last words dont match --> last line is misplaced/mismatched --> false positive
                if not check_if_last_words_match(description, truth_description):
                    accuracy["description_falsePositive"] += 1

                if startDate == truth_startDate:
                    accuracy["startDate_truePositive"] += 1
                elif startDate == "":
                    accuracy["startDate_falseNegative"] += 1
                else:
                    accuracy["startDate_falsePositive"] += 1

                if endDate == truth_endDate:
                    accuracy["endDate_truePositive"] += 1
                elif endDate == "":
                    accuracy["endDate_falseNegative"] += 1
                else:
                    accuracy["endDate_falsePositive"] += 1
                break
        if not corresponsing_experience_found:
            accuracy["startDate_falseNegative"] += 1
            accuracy["endDate_falseNegative"] += 1
            accuracy["description_falseNegative"] += 1
    return accuracy


def match_descriptions(fulltext_truth, description_exported):
    if fulltext_truth == "":
        if description_exported == "":
            return True
        else:
            return False

    # Take longest sentence
    longest_line_in_truth_text = max(sent_tokenize(fulltext_truth), key=len)
    longest_line_in_truth_text = clean_text(clean_text_from_nonbasic_characters(longest_line_in_truth_text))

    fulltext_description = ""
    for sentence in description_exported:
        fulltext_description += sentence

    fulltext_description = clean_text(clean_text_from_nonbasic_characters(fulltext_description))

    times_to_match = len(longest_line_in_truth_text.split(" "))
    for word in longest_line_in_truth_text.split(" "):
        match = re.search(clean_for_comparison(word).lower(), clean_for_comparison(fulltext_description).lower())
        if match is not None:
            times_to_match = times_to_match - 1
    return times_to_match == 0


def check_if_last_words_match(description, fulltext_truth):
    fulltext_experience = ""
    for line in description:
        fulltext_experience += line

    fulltext_truth = clean_for_comparison(fulltext_truth).lower()
    fulltext_experience = clean_for_comparison(fulltext_experience).lower()

    # Get last 10 words from cleaned descriptions
    fulltext_truth_array = fulltext_truth.split(" ")[-10:]
    fulltext_experience_array = fulltext_experience.split(" ")[-10:]

    # Check if 7 out of 10 matches or len(fulltext_truth_array) - 3) matches
    match_counter = 0
    for word in fulltext_experience_array:
        if word in fulltext_truth_array:
            match_counter += 1

    if match_counter >= len(fulltext_truth_array) - 3:
        return True
    return False


def compare_skills(json_groundtruth, json_corresponding_export, accuracy):
    if "skills" not in json_groundtruth or "Skills" not in json_corresponding_export or "SkillsRecognizedInSkillSection" not in json_corresponding_export:
        return accuracy

    full_skills_text_extracted = ""
    for line in json_corresponding_export["Skills"]:
        full_skills_text_extracted += line
    full_skills_text_extracted = clean_text_for_skill_extraction(full_skills_text_extracted.lower())

    list_of_skills_in_groundtruth =  []
    for skillDict in json_groundtruth["skills"]:
        if "keywords" in skillDict:
            list_of_skills_in_groundtruth.append(skillDict["keywords"])
    list_of_skills_in_groundtruth = [item.lower() for sublist in list_of_skills_in_groundtruth for item in sublist]

    found_skills = []
    for skill in list_of_skills_in_groundtruth:
        skill = skill.lower()
        if (full_skills_text_extracted.find(skill) != -1):
            accuracy["skilltext_truePositive"] += 1
        else:
            accuracy["skilltext_falseNegative"] += 1

        if skill in [skill.lower() for skill in json_corresponding_export["SkillsRecognizedInSkillSection"]]:
            accuracy["skillextracted_truePositive"] += 1
            found_skills.append(skill)
        else:
            accuracy["skillextracted_falseNegative"] += 1

    list_of_falsePositives = [x for x in json_corresponding_export["SkillsRecognizedInSkillSection"] if x not in found_skills]
    accuracy["skillextracted_falsePositive"] += len(list_of_falsePositives)
    return accuracy


if __name__ == "__main__":
    accuracy = start()
    startDate_truePositive = accuracy["startDate_truePositive"]
    startDate_falsePositive = accuracy["startDate_falsePositive"]
    startDate_falseNegative = accuracy["startDate_falseNegative"]
    endDate_truePositive = accuracy["endDate_truePositive"]
    endDate_falsePositive = accuracy["endDate_falsePositive"]
    endDate_falseNegative = accuracy["endDate_falseNegative"]
    description_truePositive = accuracy["description_truePositive"]
    description_falsePositive = accuracy["description_falsePositive"]
    description_falseNegative = accuracy["description_falseNegative"]
    skilltext_truePositive = accuracy["skilltext_truePositive"]
    skilltext_falseNegative = accuracy["skilltext_falseNegative"]
    skillextracted_truePositive = accuracy["skillextracted_truePositive"]
    skillextracted_falseNegative = accuracy["skillextracted_falseNegative"]
    skillextracted_falsePositive = accuracy["skillextracted_falsePositive"]

    evaluation = """
        startDate
            precision: {}
            recall: {}
        endDate
            precision: {}
            recall: {}
        description
            precision: {}
            recall: {}
        skillText
            precision: {}
            recall: {}
        skillsExtracted
            precision: {}
            recall: {}      
    """

    start_date_pos = startDate_falsePositive + startDate_truePositive
    start_date_fneg_tpos = startDate_truePositive + startDate_falseNegative

    end_date_pos = endDate_falsePositive + endDate_truePositive
    end_date_fneg_tpos = endDate_truePositive + endDate_falseNegative

    descr_pos = description_truePositive + description_falsePositive
    descr_fneg_tpos = description_falseNegative + description_truePositive

    skilltext_pos = skilltext_truePositive #Skilltext doesnt have false pos.
    skilltext_fneg_tpos = skilltext_falseNegative + skilltext_truePositive

    skillextracted_pos = skillextracted_truePositive + skillextracted_falsePositive
    skillextracted_fneg_tpos = skillextracted_falseNegative + skillextracted_truePositive

    print(evaluation.format(
        0 if (startDate_truePositive == 0 or start_date_pos == 0) else startDate_truePositive / start_date_pos,
        0 if (startDate_truePositive == 0 or start_date_fneg_tpos == 0) else startDate_truePositive / start_date_fneg_tpos,

        0 if (endDate_truePositive == 0 or end_date_pos == 0) else endDate_truePositive / end_date_pos,
        0 if (endDate_truePositive == 0 or end_date_fneg_tpos == 0) else endDate_truePositive / end_date_fneg_tpos,

        0 if (description_truePositive == 0 or descr_pos == 0) else description_truePositive / descr_pos,
        0 if (description_truePositive == 0 or descr_fneg_tpos == 0) else description_truePositive / descr_fneg_tpos,

        0 if (skilltext_truePositive == 0 or skillextracted_pos == 0) else skilltext_truePositive / skilltext_pos,
        0 if (skilltext_truePositive == 0 or skilltext_fneg_tpos == 0) else skilltext_truePositive / skilltext_fneg_tpos,

        0 if (skillextracted_pos == 0 or skillextracted_pos == 0) else skillextracted_truePositive / skillextracted_pos,
        0 if (skillextracted_pos == 0 or skillextracted_fneg_tpos == 0) else skillextracted_truePositive / skillextracted_fneg_tpos
    ))
