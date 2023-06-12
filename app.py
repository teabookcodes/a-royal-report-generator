# Importy knihoven
import os
import requests
import json
import csv
import datetime
import re
from dotenv import load_dotenv
from fpdf import FPDF

load_dotenv()

# Získej aktuální čas, odečti od něj 24 hodin a převeď jej na UNIX timestamp v požadovaném formátu
current_time = datetime.datetime.now()

time_24_hours_ago = current_time - datetime.timedelta(hours=24)

unix_timestamp = int(time_24_hours_ago.timestamp() * 1000)

# Definice konstant a proměnných
API_URL = os.getenv('API_URL')
API_TOKEN = os.getenv('API_TOKEN')
TENANT_ID = os.getenv('TENANT_ID')
# TIMESTAMP = unix_timestamp
TIMESTAMP = "1686520800000"  # Pondělí 12.6. 00:00
SEARCH_QUERY = f"occurrenceTime=gt={TIMESTAMP}"

headers = {"X-Durable-Access-Token": API_TOKEN,
           "X-Effective-Tenant-Id": TENANT_ID,
           "X-Query": SEARCH_QUERY}

# GET request pro stažení dat z API
response = requests.get(url=API_URL, headers=headers)

if response.status_code == 200:
    with open('api_data.json', 'w', encoding='utf-8') as file:
        json_data = json.dumps(response.json(), ensure_ascii=False)
        file.write(json_data)

    print("API data byla úspěšně stažena a uložena do JSON souboru.")
else:
    print("API request selhal s chybou:", response.status_code)

# - file log (datetime + request response)

# Transformace stažených dat do správného formátu

# Načti JSON data ze souboru api_data.json
with open('./api_data.json') as file:
    data = json.load(file)

# Filtruj data pro první soubor
filtered_data_a = [instance for instance in data if instance['name'] in [
    "1 - Nakládka:", "4 - Odjezd:"]]

# Vytvoř první CSV soubor s filtrovanými daty
csv_file_a = open('report-nakladka.csv', 'w', newline='')
csv_writer_a = csv.writer(csv_file_a)

# Vytvoř header tabulky pro první soubor
csv_writer_a.writerow(['Id', 'Datum a čas události',
                      'Událost', 'SPZ tahače/vozidla'])

# Vypiš řádky dat pro první soubor
for info in filtered_data_a:
    occurrence_time = datetime.datetime.fromtimestamp(
        info['occurrenceTime'] / 1000)  # Konvertuj na sekundy
    formatted_time = occurrence_time.strftime(
        '%d. %m. %Y %H:%M:%S')  # Cílový formát data
    spz = re.sub(r'\s|\.|-|:', '',
                 info['fieldInstances'][0]['textValue']).upper()
    csv_writer_a.writerow([info['id'], formatted_time,
                          info['name'], spz])

# Zavři první CSV soubor
csv_file_a.close()

# Filtruj data pro druhý soubor
filtered_data_b = [instance for instance in data if instance['name'] in [
    "2 - Vykládka:", "4 - Odjezd:"]]

# Vytvoř druhý CSV soubor s filtrovanými daty
csv_file_b = open('report-vykladka.csv', 'w', newline='')
csv_writer_b = csv.writer(csv_file_b)

# Vytvoř header tabulky pro druhý soubor
csv_writer_b.writerow(['Id', 'Datum a čas události',
                      'Událost', 'SPZ tahače/vozidla'])

# Vypiš řádky dat pro druhý soubor
for info in filtered_data_b:
    occurrence_time = datetime.datetime.fromtimestamp(
        info['occurrenceTime'] / 1000)  # Konvertuj na sekundy
    formatted_time = occurrence_time.strftime(
        '%d. %m. %Y %H:%M:%S')  # Cílový formát data
    spz = re.sub(r'\s|\.|-|:', '',
                 info['fieldInstances'][0]['textValue']).upper()
    csv_writer_b.writerow([info['id'], formatted_time,
                          info['name'], spz])

# Zavři druhý CSV soubor
csv_file_b.close()

print("Data úspěšně roztříděna a zapsána do CSV souborů.")

# - file log (datetime + error?)

# Vygenerování PDF reportů pro každou skupinu dat

# Načti CSV data
data_a = []
with open('report-nakladka.csv', 'r', encoding='utf-8') as file_a:
    csv_reader_a = csv.reader(file_a)
    for row in csv_reader_a:
        data_a.append(row)

data_b = []
with open('report-vykladka.csv', 'r', encoding='utf-8') as file_b:
    csv_reader_b = csv.reader(file_b)
    for row in csv_reader_b:
        data_b.append(row)

# Vytvoř PDF šablonu
pw = 210  # šířka stránky v mm
from_time = time_24_hours_ago.strftime('%d. %m. %Y %H:%M:%S')
creation_time = current_time.strftime('%d. %m. %Y %H:%M:%S')


class PDFA(FPDF):
    def header(self):
        # Logo
        self.image('aroyal-logo.png', 10, 8, 24)
        self.set_font('Arial', 'B', 16)
        self.cell(80)
        # Title
        self.cell(30, 10, 'Report - VYDEJ (Nakladka)', 0, 0, 'C')
        # Line break
        self.ln(40)

    # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font('Arial', '', 12)
        # Page number
        self.cell(0, 10, 'Stranka ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')


# # Vytvoř nový PDF dokument pro první soubor
pdf = PDFA()
pdf.alias_nb_pages()
pdf.add_page()
pdf.set_font('Arial', 'B', 32)
pdf.cell(w=0, h=20, txt="Objekt: DHL - Jazlovice", ln=1)
pdf.set_font('Arial', 'B', 24)
pdf.cell(w=0, h=20, txt="VOZIDLA - VYDEJ (Nakladka)", ln=1)
pdf.set_font('Arial', '', 16)
pdf.cell(w=70, h=8, txt="Datum vytvoreni reportu: ", ln=0)
pdf.cell(w=80, h=8, txt=f'{creation_time}', ln=1)
pdf.cell(w=70, h=8, txt="Casovy interval reportu: ", ln=0)
pdf.cell(w=80, h=8, txt=f'{from_time} - {creation_time}', ln=1)

# Generate pages with tables for each unique 'SPZ tahace/vozidla' value
unique_values_a = set(row[3] for row in data_a[1:])
sorted_values_a = sorted(unique_values_a, key=lambda value: next(
    row[1] for row in data_a if row[3] == value and row[2] == "1 - Nakládka:"))

for value in sorted_values_a:
    # Filter data for the current value
    filtered_data_a = [row for row in data_a if row[3] == value]

    # Extract relevant information for the table
    nakladka_timestamp = ""
    odjezd_timestamp = ""

    for row in filtered_data_a:
        if row[2] == "1 - Nakládka:":
            nakladka_timestamp = row[1]
        elif row[2] == "4 - Odjezd:":
            odjezd_timestamp = row[1]

    # Add the table to the PDF document
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(w=0, h=10, txt=f"SPZ tahace/vozidla: {value}", ln=1)
    pdf.ln(5)

    pdf.set_font('Arial', '', 16)

    pdf.cell(40, 10, "Nakladka:", 0)
    pdf.cell(40, 10, nakladka_timestamp, 0)
    pdf.ln(10)
    pdf.cell(40, 10, "Odjezd:", 0)
    pdf.cell(40, 10, odjezd_timestamp, 0)
    pdf.ln(10)

pdf.output(f'./report-nakladka.pdf', 'F')


class PDFB(FPDF):
    def header(self):
        # Logo
        self.image('aroyal-logo.png', 10, 8, 24)
        self.set_font('Arial', 'B', 16)
        self.cell(80)
        # Title
        self.cell(30, 10, 'Report - PRIJEM (Vykladka)', 0, 0, 'C')
        # Line break
        self.ln(40)

    # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font('Arial', '', 12)
        # Page number
        self.cell(0, 10, 'Stranka ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')


# # Vytvoř nový PDF dokument pro druhý soubor
pdf = PDFB()
pdf.alias_nb_pages()
pdf.add_page()
pdf.set_font('Arial', 'B', 32)
pdf.cell(w=0, h=20, txt="Objekt: DHL - Jazlovice", ln=1)
pdf.set_font('Arial', 'B', 24)
pdf.cell(w=0, h=20, txt="VOZIDLA - PRIJEM (Vykladka)", ln=1)
pdf.set_font('Arial', '', 16)
pdf.cell(w=70, h=8, txt="Datum vytvoreni reportu: ", ln=0)
pdf.cell(w=80, h=8, txt=f'{creation_time}', ln=1)
pdf.cell(w=70, h=8, txt="Casovy interval reportu: ", ln=0)
pdf.cell(w=80, h=8, txt=f'{from_time} - {creation_time}', ln=1)

# Generate pages with tables for each unique 'SPZ tahace/vozidla' value
unique_values_b = set(row[3] for row in data_b[1:])
sorted_values_b = sorted(unique_values_b, key=lambda value: next(
    (row[1] for row in data_b if row[3] == value and row[2] == "2 - Vykládka:"), ""))

for value in sorted_values_b:
    # Filter data for the current value
    filtered_data_b = [row for row in data_b if row[3] == value]

    # Check if the SPZ group has a non-empty "2 - Vykládka:" value
    if any(row[2] == "2 - Vykládka:" for row in filtered_data_b):
        # Extract relevant information for the table
        vykladka_timestamp = ""
        odjezd_timestamp = ""

        for row in filtered_data_b:
            if row[2] == "2 - Vykládka:":
                vykladka_timestamp = row[1]
            elif row[2] == "4 - Odjezd:":
                odjezd_timestamp = row[1]

        # Add the table to the PDF document
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(w=0, h=10, txt=f"SPZ tahace/vozidla: {value}", ln=1)
        pdf.ln(5)

        pdf.set_font('Arial', '', 16)

        pdf.cell(40, 10, "Vykladka:", 0)
        pdf.cell(40, 10, vykladka_timestamp, 0)
        pdf.ln(10)
        pdf.cell(40, 10, "Odjezd:", 0)
        pdf.cell(40, 10, odjezd_timestamp, 0)
        pdf.ln(10)

pdf.output(f'./report-vykladka.pdf', 'F')

print("PDF soubory byly úspěšně vytvořeny.")

# - file log (datetime + error?)

# Odeslání reportů na email

# - file log (datetime + error?)
