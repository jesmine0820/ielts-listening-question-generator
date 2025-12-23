import os
import fitz
import easyocr
import json
import google.generativeai as genai

from datetime import datetime
from fpdf import FPDF
from config.setting import model

reader = easyocr.Reader(['en'])

def get_ielts_grade(mark_str):
    try:
        score = int(mark_str.split('/')[0])
        if score >= 39: return "9.0"
        if score >= 37: return "8.5"
        if score >= 35: return "8.0"
        if score >= 32: return "7.5"
        if score >= 30: return "7.0"
        if score >= 26: return "6.5"
        if score >= 23: return "6.0"
        if score >= 18: return "5.5"
        if score >= 16: return "5.0"
        if score >= 13: return "4.5"
        return "4.0 or below"
    except:
        return "N/A"
    
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return text

def extract_text_from_upload(file_path):
    if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        results = reader.readtext(file_path, detail=0)
        return " ".join(results)
    elif file_path.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    return ""

def mark_batch_answers(official_key_text, student_data_list):
    # Format student data for the prompt
    students_input_str = ""
    for i, text in enumerate(student_data_list):
        students_input_str += f"\n--- STUDENT {i+1} ---\n{text}\n"

    prompt = f"""
    You are an IELTS Examiner. Use the provided Official Question Set as the absolute source of truth.
    
    OFFICIAL SET (Questions and Answers):
    {official_key_text}
    
    TASK:
    Mark the following {len(student_data_list)} students.
    1. Identify each candidate's name.
    2. Mark their answers (1 to 40).
    3. Calculate total marks.
    
    STUDENT INPUTS:
    {students_input_str}
    
    OUTPUT FORMAT (Strict JSON Array of Objects):
    [
      {{
        "candidate_name": "Full Name",
        "total_marks": "X/40",
        "correct_answers": {{ "1": "val" }},
        "incorrect_answers": {{ "3": {{ "student_answer": "val", "correct_answer": "val" }} }}
      }}
    ]
    """
    response = model.generate_content(prompt)
    return response.text

def export_results_to_pdf(results, official_file_path, output_filename="Marking_Summary.pdf"):
    folder_dir = os.path.dirname(official_file_path)
    folder_name = os.path.basename(folder_dir.rstrip('/'))
    set_label = folder_name.replace("set", "Set ")
    current_time = datetime.now().strftime("%d %B %Y, %I:%M %p")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 15, txt=set_label, ln=True, align='C')
    pdf.set_font("Arial", 'I', 11)
    pdf.cell(0, 5, txt=current_time, ln=True, align='C')
    pdf.ln(10)
    
    # Table Header
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(231, 16, 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(90, 12, txt=" Candidate Name", border=1, ln=0, fill=True)
    pdf.cell(50, 12, txt=" Mark", border=1, ln=0, fill=True, align='C')
    pdf.cell(50, 12, txt=" Grade (Band)", border=1, ln=1, fill=True, align='C')
    
    # Table Rows
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(0, 0, 0)
    for entry in results:
        name = entry.get("candidate_name", "Unknown")
        mark = entry.get("total_marks", "0/40")
        grade = get_ielts_grade(mark)
        pdf.cell(90, 10, txt=f" {name}", border=1, ln=0)
        pdf.cell(50, 10, txt=str(mark), border=1, ln=0, align='C')
        pdf.cell(50, 10, txt=str(grade), border=1, ln=1, align='C')

    pdf.output(output_filename)
    print(f"\n--- PDF Report Generated: {output_filename} ---")
