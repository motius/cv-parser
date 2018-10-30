# cv-parser

## Introduction

Traditional open-source parsers accomplish resume parsing, by extracting and cleaning the text, only to apply a rule-based approach to extract the necessary information. The approach in itself is not flawed, however these parsers tend to focus on information extraction, rather than making sure that the text is clean and well structured. Namely these resume parsers lose structural information such as font-size, font-color or tabbing and thus lose the ability to precisely identify sections (skills section, work experience section), as well as individual work experiences.

The goal of the project was to develop a resume parser that heavily relies on the structural and visual information of the resume. The final product converts the pdf resume to html (using pdf2htmlEx), and then applies web scraping technologies to identify sections using the resume’s structural and visual information such as font-size, font-color, bottom-margin, left-margin etc.

## Open tasks

* Add flask server with REST API
* Finish Dockerfile & add docker-compose
* Add a full setup guide to this documentation
* ... Keep improving the parser!

### Credit

All the credit for the parser itself goes to [Tamas](https://github.com/orgs/motius/people/TamasNeumer). I just built the infrastructure around it to make life easier.
