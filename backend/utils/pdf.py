from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import io
import os

def generate_prescription_pdf(doctor_name, department, patient_name, age, gender, date, time):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 50, "CITY HOSPITAL")
    
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 70, "123 Health Avenue, Wellness City")
    c.drawCentredString(width / 2, height - 85, "Phone: +1 234 567 890")

    c.setLineWidth(1)
    c.line(50, height - 100, width - 50, height - 100)

    # Doctor Details
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 130, f"Dr. {doctor_name}")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 145, f"Department: {department}")

    # Appointment Details
    c.drawString(400, height - 130, f"Date: {date}")
    c.drawString(400, height - 145, f"Time: {time}")

    c.line(50, height - 160, width - 50, height - 160)

    # Patient Details
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 180, "Patient Details:")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 200, f"Name: {patient_name}")
    c.drawString(300, height - 200, f"Age: {age}")
    c.drawString(450, height - 200, f"Gender: {gender}")

    c.line(50, height - 220, width - 50, height - 220)

    # Blank Sections
    y = height - 250
    sections = ["Diagnosis", "Medicines", "Dosage", "Notes"]
    
    for section in sections:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, f"{section}:")
        y -= 25
        # Draw lines for writing
        for _ in range(3):
            c.setLineWidth(0.5)
            c.setStrokeColor(colors.lightgrey)
            c.line(50, y, width - 50, y)
            y -= 25
        y -= 20

    # Footer
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, 50, "This is a computer generated document.")
    c.drawString(400, 50, "Doctor's Signature: ________________")

    c.save()
    buffer.seek(0)
    return buffer
