# Import necessary libraries
import os
import re
import json

from datetime import datetime
from fpdf import FPDF

# Configurations
TEMP_JSON = "model_training/generated_questions/temp_generated_questions.json"

DEJAVUSANS_FONT = "frontend/fonts/DejaVuSans.ttf"
SPACEMONO_FONT = "frontend/fonts/SpaceMono-Regular.ttf"

IELTS_LOGO = "frontend/static/images/ielts_logo.png"

# Determine next set folder
# Make sure the the folder exists
base_folder = "sets"
os.makedirs(base_folder, exist_ok=True)

# Find existing set numbers
existing = [int(re.search(r"set(\d+)", d).group(1)) for d in os.listdir(base_folder) if re.match(r"set\d+", d)]
next_set = max(existing, default=0) + 1
set_folder = os.path.join(base_folder, f"set{next_set}")
os.makedirs(set_folder, exist_ok=True)

def get_key_and_sections():
    with open(TEMP_JSON, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("JSON root must be a dict containing the timestamp key.")

    # Extract first key
    key = next(iter(data.keys()))
    raw_sections = data[key]

    # normalize section list
    sections = []
    for item in raw_sections:
        if isinstance(item, str):
            sections.append(json.loads(item))
        else:
            sections.append(item)

    return key, sections

def format_date_from_key(key):
    date_part = "_".join(key.split("_")[:3])
    date_obj = datetime.strptime(date_part, "%Y_%m_%d")
    return date_obj.strftime("%d %B %Y") 

class PDF(FPDF):
    LEFT_CONTENT_MARGIN = 20 

    # Header
    def header(self):
        if self.page_no() > 1:  
            self.image(IELTS_LOGO, x=20, y=20, w=20)
        self.set_y(30)

    # Title
    def title_page(self, set_number, date_str):
        self.set_line_width(0.8)
        self.rect(10, 10, 190, 277)

        self.image(IELTS_LOGO, x=(210 - 65) / 2, y=28, w=65)

        self.set_y(95)
        self.set_font("DejaVu", "B", 30)
        self.multi_cell(0, 12, "Listening Test", align="C")
        self.ln(4)

        self.set_font("DejaVu", "", 16)
        self.multi_cell(0, 10, f"Set {set_number}", align="C")
        self.ln(2)

        self.set_font("DejaVu", "", 12)
        self.multi_cell(0, 8, date_str, align="C")
        self.ln(10)

        # Instruction box
        box_x = 20
        box_y = 150
        box_w = 170
        box_h = 60

        self.set_line_width(0.6)
        self.rect(box_x, box_y, box_w, box_h)

        self.set_xy(box_x + 10, box_y + 10)
        self.set_font("DejaVu", "", 11)
        instructions_text = (
            "• You will hear four recordings.\n"
            "• Write your answers on the question paper.\n"
            "• You will have time to read the questions before you listen.\n"
            "• Use a pencil. Write clearly and follow instructions.\n"
            "• At the end, you will have 10 minutes to transfer your answers."
        )
        self.multi_cell(box_w - 20, 6, instructions_text)

        self.add_page()

    # Part Header
    def part_header(self, part_number):
        self.set_font("DejaVu", "B", 16)
        self.set_x(self.LEFT_CONTENT_MARGIN)
        self.multi_cell(0, 10, f"Part {part_number}", align="L")
        self.ln(5)

    # Instructions
    def write_instructions(self, instructions):
        self.set_x(self.LEFT_CONTENT_MARGIN)
        self.set_font("DejaVu", "", 12)
        self.multi_cell(0, 6, instructions)
        self.ln(4)

    # Body
    # 1. Question only
    def write_questions(self, questions):
        self.set_font("DejaVu", "", 10)
        for q in questions:
            self.set_x(self.LEFT_CONTENT_MARGIN)
            self.multi_cell(0, 6, q)
        self.ln(4)

    # 2. MCQ
    def write_mcq(self, questions, options):
        self.set_x(self.LEFT_CONTENT_MARGIN)
        self.set_font("DejaVu", "", 10)
        for q in questions:
            self.set_x(self.LEFT_CONTENT_MARGIN)
            self.multi_cell(0, 6, f"{q}")
            for o in options:
                self.set_x(self.LEFT_CONTENT_MARGIN)
                self.multi_cell(0, 6, f"{o}")
        self.ln(4)

    # 3. Matching
    def write_matching(self, questions, options):
        self.set_font("DejaVu", "", 10)
        self.set_x(self.LEFT_CONTENT_MARGIN)
        self.multi_cell(0, 6, "-----------------------------------------")
        for o in options:
            self.set_x(self.LEFT_CONTENT_MARGIN)
            self.multi_cell(0, 6, f"{o}")
        self.set_x(self.LEFT_CONTENT_MARGIN)
        self.multi_cell(0, 6, "-----------------------------------------")
        self.ln(2)

        for q in questions:
            self.set_x(self.LEFT_CONTENT_MARGIN)
            self.multi_cell(0, 6, f"{q}: ____________________")
        self.ln(4)

    # 4. With Diagram
    def write_diagram(self, diagram, questions):
        self.set_x(self.LEFT_CONTENT_MARGIN)
        self.set_font("SpaceMono", "", 8)
        self.multi_cell(0, 3, diagram)
        self.set_font("DejaVu", "", 10)
        self.ln(2)
        for q in questions:
            self.set_x(self.LEFT_CONTENT_MARGIN)
            self.multi_cell(0, 6, f"{q}. ____________________")
        self.ln(4)

    # 5. Form Completion
    def write_form(self, diagram):
        self.set_x(self.LEFT_CONTENT_MARGIN)
        self.set_font("SpaceMono", "", 8)
        self.multi_cell(0, 3, diagram)
        self.set_font("DejaVu", "", 10)
        self.ln(2)
        self.ln(4)

    # Answers
    def write_answers(self):
        self.set_x(self.LEFT_CONTENT_MARGIN)
        self.set_font("DejaVu", "B", 14)
        self.multi_cell(0, 6, "Answers")
        self.ln(2)

    def write_answers_line(self, answers):
        self.set_font("DejaVu", "", 11)
        line_height = 6
        bottom_margin = 25

        for num, ans in answers:
            self.set_x(self.LEFT_CONTENT_MARGIN)
            full_text = f"{num}. {ans}"

            block_height = line_height

            if self.get_y() + block_height + bottom_margin > self.h:
                self.add_page()
                self.set_x(self.LEFT_CONTENT_MARGIN)

            self.multi_cell(0, line_height, full_text)
            self.ln(2)
            
        self.set_x(self.LEFT_CONTENT_MARGIN)
        self.ln(4)

    # Transcript
    def write_transcripts(self):
        self.set_x(self.LEFT_CONTENT_MARGIN)
        self.set_font("DejaVu", "B", 14)
        self.multi_cell(0, 6, "Transcripts")
        self.ln(2)

    def write_transcripts_line(self, transcripts):
        self.set_font("DejaVu", "", 11)

        paragraphs = transcripts.split("\n")
        line_height = 6
        bottom_margin = 25

        for para in paragraphs:
         
            effective_width = self.w - self.r_margin - self.l_margin
        
            approx_char_per_line = int(effective_width / (self.get_string_width("A") * 1.05))
            lines_needed = max(1, (len(para) // approx_char_per_line) + 1)
            block_height = lines_needed * line_height

            if self.get_y() + block_height + bottom_margin > self.h:
                self.add_page()

            self.multi_cell(0, line_height, para)
            self.ln(2)

    # Footer
    def footer(self):
        self.set_line_width(0.8)
        self.rect(10, 10, 190, 277)
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    # Break Line
    def break_line(self):
        self.set_x(self.LEFT_CONTENT_MARGIN)
        self.set_font("DejaVu", "B", 14)
        self.multi_cell(0, 6, "-------------------------------------------------------------------------------------------")
        self.ln(2)

# Full Set -> Question + Answers + Transcript PDF
def export_full_pdf():
    key, sections = get_key_and_sections()
    formatted_date = format_date_from_key(key)
    full_pdf_path = os.path.join(set_folder, "full_set.pdf")

    pdf = PDF()
    pdf.add_font("DejaVu", "", DEJAVUSANS_FONT, uni=True)
    pdf.add_font("DejaVu", "B", DEJAVUSANS_FONT, uni=True)
    pdf.add_font("SpaceMono", "", SPACEMONO_FONT, uni=True)

    pdf.set_left_margin(25)
    pdf.set_right_margin(25)
    pdf.set_top_margin(10)

    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.alias_nb_pages() 
    
    pdf.add_page()
    pdf.title_page(next_set, formatted_date)

    next_section = None
    first_part = True

    for section in sections:
        section_num = str(section.get("Section", "")).strip()
        instructions = section.get("Instructions", "")
        questions = section.get("Questions", [])
        diagram = section.get("Diagram", "")
        options = section.get("Options", [])
        type_code = section.get("Type").split()[0]

        # Track section
        current_section = section_num

        if not first_part:
            pdf.add_page()
        first_part = False

        if current_section != next_section:
            pdf.part_header(section_num)

        pdf.write_instructions(instructions)

        if type_code in ["T001", "T003", "T004", "T008", "T011"]:
            if diagram and diagram.strip() != "":
                pdf.write_diagram(diagram, questions)
            else:
                pdf.write_questions(questions)

        if type_code in ["T005", "T007"]:
            pdf.write_mcq(questions, options)

        if type_code in ["T006"]:
            pdf.write_matching(questions, options)

        if type_code in ["T009", "T010"]:
            pdf.write_questions(questions)

        if type_code in ["T002"]:
            pdf.write_form(diagram)

        next_section = section_num

    # Print Answers
    pdf.add_page()
    question_number = 1
    pdf.write_answers()

    for section in sections:
        section_num = str(section.get("Section", "")).strip()
        answers = section.get("Answers", [])

        pdf.part_header(section_num)

        for ans in answers:
            pdf.write_answers_line([(question_number, ans)])
            question_number += 1

        pdf.break_line()

    # Print Transcripts
    pdf.add_page()
    pdf.write_transcripts()

    for section in sections:
        section_num = str(section.get("Section", "")).strip()
        transcripts = section.get("Transcript", "")

        pdf.part_header(section_num)

        pdf.write_transcripts_line(transcripts)
        pdf.break_line()

    pdf.output(full_pdf_path)

# 2. Questoins Only PDF
def export_questions_pdf():
    key, sections = get_key_and_sections()
    formatted_date = format_date_from_key(key)
    questions_pdf_path = os.path.join(set_folder, "questions.pdf")

    pdf = PDF()
    pdf.add_font("DejaVu", "", DEJAVUSANS_FONT, uni=True)
    pdf.add_font("DejaVu", "B", DEJAVUSANS_FONT, uni=True)
    pdf.add_font("SpaceMono", "", SPACEMONO_FONT, uni=True)

    pdf.set_left_margin(25)
    pdf.set_right_margin(25)
    pdf.set_top_margin(10)

    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.alias_nb_pages() 
    
    pdf.add_page()
    pdf.title_page(set_number=1, date_str=formatted_date)

    next_section = None
    first_part = True

    for section in sections:
        section_num = str(section.get("Section", "")).strip()
        instructions = section.get("Instructions", "")
        questions = section.get("Questions", [])
        diagram = section.get("Diagram", "")
        options = section.get("Options", [])
        type_code = section.get("Type").split()[0]

        # Track section
        current_section = section_num

        if not first_part:
            pdf.add_page()
        first_part = False

        if current_section != next_section:
            pdf.part_header(section_num)

        pdf.write_instructions(instructions)

        if type_code in ["T001", "T003", "T004", "T008", "T011"]:
            if diagram and diagram.strip() != "":
                pdf.write_diagram(diagram, questions)
            else:
                pdf.write_questions(questions)

        if type_code in ["T005", "T007"]:
            pdf.write_mcq(questions, options)

        if type_code in ["T006"]:
            pdf.write_matching(questions, options)

        if type_code in ["T009", "T010"]:
            pdf.write_questions(questions)

        if type_code in ["T002"]:
            pdf.write_form(diagram)

        next_section = section_num

    pdf.output(questions_pdf_path)

# 3. Transcript Only TXT
def export_transcript_txt():
    key, sections = get_key_and_sections()
    formatted_date = format_date_from_key(key)
    transcript_txt_path = os.path.join(set_folder, "transcript.txt")

    with open(transcript_txt_path, "w", encoding="utf-8") as file:
        # Header
        file.write("                               IELTS Listening Test \n")
        file.write(f"                                        Set {next_set}        \n")
        file.write(f"                                   {formatted_date}\n\n")

        # Body
        next_section = None

        for section in sections:

            section_num = str(section.get("Section", "")).strip()
            transcript = section.get("Transcript", "")

            # Track section
            current_section = section_num

            if current_section != next_section:
                file.write(f"Part {section_num}\n")
            else:
                file.write("\n")

            file.write(f"{transcript}\n")

            file.write(f"\n -------------------------------------------------------------------------------------------------\n")

            next_section = section_num

# 4. Questions Only TXT
def export_question_txt():
    key, sections = get_key_and_sections()
    formatted_date = format_date_from_key(key)
    question_txt_path = os.path.join(set_folder, "questions.txt")

    with open(question_txt_path, "w", encoding="utf-8") as file:

        # Header
        file.write("                               IELTS Listening Test \n")
        file.write(f"                                        Set {next_set}       \n")
        file.write(f"                                   {formatted_date}\n\n")

        # Body
        next_section = None

        for section in sections:

            section_num = str(section.get("Section", "")).strip()
            instructions = section.get("Instructions", "")
            questions = section.get("Questions", [])
            diagram = section.get("Diagram", "")
            options = section.get("Options", [])
            type_code = section.get("Type").split()[0]

            # Track section
            current_section = section_num

            if current_section != next_section:
                file.write(f"Part {section_num}\n")
            else:
                file.write("\n")

            file.write(f"{instructions}\n\n")

            if type_code in ["T001", "T003", "T004", "T008", "T011"]:
                if diagram and diagram.strip() != "":
                    file.write(f"{diagram}\n\n")
                    file.write(f"Answers: \n")
                    for q in questions:
                        file.write(f"{q}. ________________\n")
                else:
                    for q in questions:
                        file.write(f"{q}\n")

            if type_code in ["T005", "T007"]:
                if options and len(options) != 0:
                    for q in questions:
                        file.write(f"{q}\n")
                        for o in options:
                            if isinstance(o, list):  
                                o = " ".join(o)
                            file.write(f"{o}\n")
                        file.write(f"\n")

            if type_code == "T006":
                file.write(f"--------------------------------\n")
                for o in options:
                    if isinstance(o, list):  
                        o = " ".join(o)
                    file.write(f"    {o}\n")
                file.write(f"--------------------------------\n\n")
                for q in questions:
                    file.write(f"{q} _____________________\n")
            
            if type_code in ["T009", "T010"]:
                for q in questions:
                    file.write(f"{q}\n")

            if type_code in ["T002"]:
                file.write(f"{diagram}\n")

            file.write(f"\n -------------------------------------------------------------------------------------------------\n")

            next_section = section_num
 
        file.write("                               End of Paper")

