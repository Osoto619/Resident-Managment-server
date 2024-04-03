from datetime import datetime
import PySimpleGUI as sg
import random
import api_functions
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter,inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageTemplate, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
import calendar
import config
#from data import breakfast, lunch, dinner

API_URL = config.API_URL


# Custom action to add a footer
def add_footer(canvas, doc):
    footer_text = f"CareTech ADL Chart PDF Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    canvas.saveState()
    canvas.setFont('Times-Roman', 10)
    canvas.drawString(doc.leftMargin, 15, footer_text)
    canvas.restoreState()


def create_medication_list_pdf(resident_name, medications_data):
    pdf_name = f"{resident_name}_Medication_Schedule.pdf"
    doc = SimpleDocTemplate(pdf_name, pagesize=letter)
    elements = []
    styleSheet = getSampleStyleSheet()

    # Add title
    title = Paragraph(f"Medication List for {resident_name}", styleSheet['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Scheduled Medications
    if medications_data['Scheduled']:
        for timeslot, med_info in medications_data['Scheduled'].items():
            elements.append(Paragraph(timeslot, styleSheet['Heading2']))
            data = [['Medication', 'Dosage', 'Instructions']]
            for med_name, details in med_info.items():
                data.append([med_name, details['dosage'], details['instructions']])
            table = Table(data, [120, 120, 240])
            table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 12))

    # PRN Medications
    if medications_data['PRN']:
        elements.append(Paragraph("PRN (As Needed)", styleSheet['Heading2']))
        data = [['Medication', 'Dosage', 'Instructions']]
        for med_name, details in medications_data['PRN'].items():
            data.append([med_name, details['dosage'], details['instructions']])
        table = Table(data, [120, 120, 240])
        table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

    # Controlled Medications
    if medications_data['Controlled']:
        elements.append(Paragraph("Controlled Medications", styleSheet['Heading2']))
        data = [['Medication', 'Dosage', 'Instructions', 'Form']]
        for med_name, details in medications_data['Controlled'].items():
            data.append([med_name, details['dosage'], details['instructions'], details['form']])
        table = Table(data, [150, 80, 180, 60])
        table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

    doc.build(elements)
    sg.Popup('Medication List PDF Created!')


def generate_adl_chart_pdf(resident_name, year_month, adl_data):
    pdf_name = f"{resident_name}_ADL_Chart_{year_month}.pdf"
    doc = SimpleDocTemplate(pdf_name, pagesize=landscape(letter), topMargin=20, leftMargin=36, rightMargin=36, bottomMargin=36)
    elements = []
    
    # Styles for the document
    styles = getSampleStyleSheet()
    title_style = styles['Title']

    # Adding a title at the top of the document
    title = f"ADL Chart {resident_name} - {year_month}"
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 8))  # Adding some space after the title

    # Days of the month as column headers
    days_in_month = calendar.monthrange(int(year_month.split('-')[0]), int(year_month.split('-')[1]))[1]
    headers = ["ADL Activity"] + [str(day) for day in range(1, days_in_month + 1)]
    
    # ADL Activities as row headers
    adl_activities = [
        "First Shift SP", "Second Shift SP", "First Shift Activity1", "First Shift Activity2",
        "First Shift Activity3", "Second Shift Activity4", "First Shift BM", "Second Shift BM",
        "Shower", "Shampoo", "Sponge Bath", "Peri Care AM", "Peri Care PM",
        "Oral Care AM", "Oral Care PM", "Nail Care", "Skin Care", "Shave",
        "Breakfast", "Lunch", "Dinner", "Snack AM", "Snack PM", "Water Intake"
    ]
    
    # Initialize table data
    table_data = [headers]  # Adding the headers as the first row
    
    # Filling the table with ADL activities and placeholders for each day's data
    for activity in adl_activities:
        row = [activity] + ['' for _ in range(days_in_month)]  # Placeholder for each day
        table_data.append(row)
    
    print(f'adl_data: {adl_data}')
    for entry in adl_data:
        chart_date_str = entry["chart_date"]
        date_part = ' '.join(chart_date_str.split(' ')[1:4])
        chart_date = datetime.strptime(date_part, "%d %b %Y")
        day_number = chart_date.day - 1  # Adjust for 0 indexing
        for i, adl_key in enumerate(adl_activities):
            value = entry.get(adl_key.lower().replace(" ", "_"), "")
            if value:
                table_data[i + 1][day_number + 1] = value  # +1 because of headers row

    
    # Creating the table
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    elements.append(table)

    # Add some space before the activities legend
    elements.append(Spacer(1, 6))

    # # Activities legend title
    # elements.append(Paragraph("Activities", styles['Heading3']))

    # Activities list
    activities = [
        "1. Movie & Snack or TV",
        "2. Exercise/Walking",
        "3. Games/Puzzles",
        "4. Outside/Patio",
        "5. Arts & Crafts",
        "6. Music Therapy",
        "7. Gardening",
        "8. Listen to Music",
        "9. Social Hour",
        "10. Cooking/Baking",
        "11. Birdwatching",
        "12. Outing/Excursion",
        "13. Hospice Visit",
        "14. Other as Listed on the Service Plan",
        "15. Social Media"
    ]

    # Calculate the number of activities in each column (assuming 3 columns with roughly equal distribution)
    num_per_column = len(activities) // 3 + (1 if len(activities) % 3 > 0 else 0)

    # Prepare data for the table, ensuring each row has three columns
    table_data = [activities[i:i+num_per_column] for i in range(0, len(activities), num_per_column)]
    # Ensure all rows have 3 columns (fill missing with empty strings)
    for row in table_data:
        while len(row) < 3:
            row.append("")

    # Create the table for activities legend
    activities_table = Table(table_data)
    activities_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        # Adjust paddings and spacing as necessary
        ('LEFTPADDING', (0,0), (-1,-1), 1),  # Reduced padding
        ('RIGHTPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))

    # Add the table to the elements
    elements.append(activities_table)
    
    # Build and save the PDF
    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
    sg.Popup(f"PDF generated: {pdf_name}")  # Show a popup to indicate the PDF was generated

# -------------------------------------------------- Calendars -------------------------------------------------- #

class CalendarPageTemplate(PageTemplate):
    def __init__(self):
        frames = [
            Frame(
                x1=72, y1=72, width=letter[0] - 144, height=letter[1] - 144,
                leftPadding=0, rightPadding=0, bottomPadding=0, topPadding=0,
                id='normal'
            )
        ]
        super().__init__('CalendarPageTemplate', frames=frames)


    def afterDrawPage(self, canvas, doc):
        month = doc.month
        year = doc.year
        month_name = calendar.month_name[month]
        substitutions = "Substitutions: Leftovers, sandwich, soup, veggies, fruit, cottage cheese"
        snacks = "Snacks: crackers, chips, pastries, pudding, fruit, yogurt, apple sauce, ice-cream"
        canvas.setFont('Helvetica-Bold', 24)
        canvas.drawCentredString(letter[0] / 2, letter[1] - 50, f'{month_name} Menu {year}')
        canvas.setFont('Helvetica', 16)
        footer_x = 275
        footer_y_substitutions = 55
        footer_y_snacks = footer_y_substitutions - 25
        # Draw the substitutions line
        canvas.drawCentredString(footer_x, footer_y_substitutions, substitutions)
        # Draw the snacks line
        canvas.drawCentredString(footer_x + 30, footer_y_snacks, snacks)


def on_every_page(canvas, doc):
    # Retrieve month and year from the document for the header
    month_name = calendar.month_name[doc.month]
    year = doc.year

    # Define substitutions and snacks text for the footer
    substitutions = "Substitutions: Leftovers, sandwich, soup, veggies, fruit, cottage cheese"
    snacks = "Snacks: crackers, chips, pastries, pudding, fruit, yogurt, apple sauce, ice-cream"

    # Save canvas state to preserve settings
    canvas.saveState()

    # Header configuration
    canvas.setFont('Helvetica-Bold', 24)
    canvas.drawCentredString(letter[0] / 2, letter[1] - 50, f'{month_name} Menu {year}')

    # Footer configuration
    canvas.setFont('Helvetica', 16)
    footer_x_center = letter[0] / 2  # Center alignment for the footer text
    footer_y_substitutions = 55  # Y-coordinate for substitutions text
    footer_y_snacks = 30  # Y-coordinate for snacks text
    canvas.drawCentredString(footer_x_center, footer_y_substitutions, substitutions)
    canvas.drawCentredString(footer_x_center, footer_y_snacks, snacks)

    # Restore canvas state
    canvas.restoreState()


# Menu Generator Function
def create_menu(year, month):
    # Fetch meal data from the API
    breakfast = api_functions.fetch_meal_data(API_URL, 'breakfast')
    lunch = api_functions.fetch_meal_data(API_URL, 'lunch')
    dinner = api_functions.fetch_meal_data(API_URL, 'dinner')

    # Define the file name
    file_name = f"Menu-Calendar-{calendar.month_name[month]}-{year}.pdf"

    # Create a PDF document
    doc = SimpleDocTemplate(file_name, pagesize=letter)
    doc.month = month
    doc.year = year

    # # Assign the custom PageTemplate to the document
    # doc.addPageTemplates(CalendarPageTemplate())

    def meal(sequence):
        choice = random.choice(sequence)
        meal_text = ""
        for element in choice:
            meal_text += element + "\n"
        return meal_text

    # Get the calendar data for the current month
    cal = calendar.monthcalendar(year, month)

    # Define table data
    table_data = []
    headers = ['Day', 'Breakfast', 'Lunch', 'Dinner']
    table_data.append(headers)

    # Define past meals lists for breakfast. lunch, and dinner
    past_breakfast_meals = []
    past_lunch_meals = []
    past_dinner_meals = []

    for week in cal:
        for day in week:
            if day == 0:
                continue
            else:
                day_of_week = calendar.day_abbr[calendar.weekday(year, month, day)]

                # Generate unique meals for each day's breakfast, lunch, and dinner
                breakfast_choice = meal(breakfast)
                while breakfast_choice in past_breakfast_meals:
                    breakfast_choice = meal(breakfast)
                past_breakfast_meals.append(breakfast_choice)

                lunch_choice = meal(lunch)
                while lunch_choice in past_lunch_meals:
                    lunch_choice = meal(lunch)
                past_lunch_meals.append(lunch_choice)

                dinner_choice = meal(dinner)
                while dinner_choice in past_dinner_meals:
                    dinner_choice = meal(dinner)
                past_dinner_meals.append(dinner_choice)

                table_data.append([f"{day_of_week} ({day})", breakfast_choice, lunch_choice, dinner_choice])

                # Limit the size of past_meals lists to 7 days
                if len(past_breakfast_meals) > 7:
                    past_breakfast_meals.pop(0)
                if len(past_lunch_meals) > 7:
                    past_lunch_meals.pop(0)
                if len(past_dinner_meals) > 7:
                    past_dinner_meals.pop(0)

    # Create a table and add data
    table = Table(table_data, repeatRows=1)

    # Define table style
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header row background color
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),  # Header row text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center alignment for all cells
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header row font
        ('FONTSIZE', (0, 0), (-1, 0), 12),  # Header row font size
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Header row bottom padding
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Data rows background color
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Gridlines
    ])

    # Apply table style
    table.setStyle(table_style)

    # Build the PDF document with the table
    elements = [Spacer(1, 12), table]  # Add the month name and some space before the table

    # Wrapper around doc.build to manually handle onPage actions
    def build_doc(elements):
        def on_every_page_wrapper(canvas, doc):
            on_every_page(canvas, doc)
        doc.build(elements, onFirstPage=on_every_page_wrapper, onLaterPages=on_every_page_wrapper)

    build_doc(elements)

    return file_name


# Activity Generator Function
def create_calendar(year, month):
    activity_list = api_functions.fetch_activities(API_URL)

    file_name = "Activity-Calendar-{}-{}.pdf".format(calendar.month_name[month], year)
    doc = SimpleDocTemplate("Activity-Calendar-{}-{}.pdf".format(calendar.month_name[month], year), pagesize=landscape(letter), topMargin=0.1*inch)
    activities_per_day = 3
    cal = calendar.monthcalendar(year, month)
    table_data = []
    headers = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    table_data.append(headers)
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append(" ")
            else:
                day_activities = []
                day_activities.append("Current Events")
                for i in range(activities_per_day - 1):
                    activity = random.choice(activity_list)
                    while activity in day_activities:
                        activity = random.choice(activity_list)
                    day_activities.append(activity)
                week_data.append("{}:\n - {}\n - {}".format(day, day_activities[0], "\n - ".join(day_activities[1:])))
        table_data.append(week_data)

    col_widths = [1.51*inch] * 7
    row_heights = [1.07*inch] * len(table_data)
   
    table = Table(table_data, colWidths=col_widths, rowHeights=row_heights)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    title_style = ParagraphStyle(
        name='Calendar Title',
        fontSize=30,
        alignment=TA_CENTER,
        spaceAfter=10,
        spaceBefore=0
    )

    title = Paragraph(f"<font size=30><b>{calendar.month_name[month]} Activities {year}</b></font>", style=title_style)

    doc.build([Spacer(1, 0.0003*inch), title, Spacer(1, 0.5*inch), table])  # Adjust spacer heights as needed

    return file_name
