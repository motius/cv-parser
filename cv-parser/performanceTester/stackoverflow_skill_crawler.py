import requests

def stackoverflow_crawler():
    skills = []
    string_skills = ""
    for i in range(10):
        r = requests.get('https://api.stackexchange.com/2.2/tags?page='
                         + str(i+1) +
                         '&pagesize=100&order=desc&sort=popular&site=stackoverflow')
        json_content = r.json()
        for item in json_content["items"]:
            skills.append(item["name"])
            string_skills += (item["name"] + '\n')
    print(string_skills)
    return skills

if __name__ == "__main__":
    stackoverflow_crawler()
