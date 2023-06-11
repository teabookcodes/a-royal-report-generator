# Importy knihoven
import os
import requests
import json
import csv
import datetime
import re
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

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
TIMESTAMP = "1686261600000"  # Pátek 9.6. 00:00
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
csv_file_a = open('report-a.csv', 'w', newline='')
csv_writer_a = csv.writer(csv_file_a)

# Vytvoř header tabulky pro první soubor
csv_writer_a.writerow(['ID', 'Datum a cas udalosti',
                      'Udalost', 'SPZ tahace/vozidla'])

# Vypiš řádky dat pro první soubor
for info in filtered_data_a:
    occurrence_time = datetime.datetime.fromtimestamp(
        info['occurrenceTime'] / 1000)  # Konvertuj na sekundy
    formatted_time = occurrence_time.strftime(
        '%Y-%m-%d %H:%M:%S')  # Cílový formát data
    spz = re.sub(r'[\s.-]', '', info['fieldInstances'][0]['textValue']).upper()
    csv_writer_a.writerow([info['id'], formatted_time,
                          info['name'], spz])

# Zavři první CSV soubor
csv_file_a.close()

# Filtruj data pro druhý soubor
filtered_data_b = [instance for instance in data if instance['name'] in [
    "2 - Vykládka:", "4 - Odjezd:"]]

# Vytvoř druhý CSV soubor s filtrovanými daty
csv_file_b = open('report-b.csv', 'w', newline='')
csv_writer_b = csv.writer(csv_file_b)

# Vytvoř header tabulky pro druhý soubor
csv_writer_b.writerow(['ID', 'Datum a cas udalosti',
                      'Udalost', 'SPZ tahace/vozidla'])

# Vypiš řádky dat pro druhý soubor
for info in filtered_data_b:
    occurrence_time = datetime.datetime.fromtimestamp(
        info['occurrenceTime'] / 1000)  # Konvertuj na sekundy
    formatted_time = occurrence_time.strftime(
        '%Y-%m-%d %H:%M:%S')  # Cílový formát data
    spz = re.sub(r'[\s.-]', '', info['fieldInstances'][0]['textValue']).upper()
    csv_writer_b.writerow([info['id'], formatted_time,
                          info['name'], spz])

# Zavři druhý CSV soubor
csv_file_b.close()

print("Data úspěšně roztříděna a zapsána do CSV souborů.")

# - file log (datetime + error?)

# Vygenerování PDF reportů pro každou skupinu dat


# Načti CSV data
data_a = []
with open('report-a.csv', 'r', encoding='utf-8') as file_a:
    csv_reader_a = csv.reader(file_a)
    for row in csv_reader_a:
        data_a.append(row)

data_b = []
with open('report-b.csv', 'r', encoding='utf-8') as file_b:
    csv_reader_b = csv.reader(file_b)
    for row in csv_reader_b:
        data_b.append(row)

# Vytvoř nový PDF dokument pro první soubor
pdf_file_a = 'report-a.pdf'
doc_a = SimpleDocTemplate(pdf_file_a, pagesize=A4)

# Vytvoř nový PDF dokument pro druhý soubor
pdf_file_b = 'report-b.pdf'
doc_b = SimpleDocTemplate(pdf_file_b, pagesize=A4)

# Získání unikátních hodnot 'SPZ tahace/vozidla' pro první soubor
unique_values_a = set(row[3] for row in data_a[1:])

# Vytvoření tabulek pro jednotlivé hodnoty 'SPZ tahace/vozidla' pro první soubor
tables_a = []
for value in unique_values_a:
    # Filtrování dat pro aktuální hodnotu
    filtered_data_a = [row for row in data_a if row[3] == value]
    # Vytvoření tabulky pro aktuální hodnotu
    table_a = Table(filtered_data_a, repeatRows=1)
    table_a.setStyle(TableStyle(
        [('GRID', (0, 0), (-1, -1), 0.5, colors.black)]))
    tables_a.append(table_a)

# Přidání tabulek do prvního PDF dokumentu
elements_a = []
for table_a in tables_a:
    elements_a.append(table_a)
doc_a.build(elements_a)

# Získání unikátních hodnot 'SPZ tahace/vozidla' pro druhý soubor
unique_values_b = set(row[3] for row in data_b[1:])

# Vytvoření tabulek pro jednotlivé hodnoty 'SPZ tahace/vozidla' pro druhý soubor
tables_b = []
for value in unique_values_b:
    # Filtrování dat pro aktuální hodnotu
    filtered_data_b = [row for row in data_b if row[3] == value]
    # Vytvoření tabulky pro aktuální hodnotu
    table_b = Table(filtered_data_b, repeatRows=1)
    table_b.setStyle(TableStyle(
        [('GRID', (0, 0), (-1, -1), 0.5, colors.black)]))
    tables_b.append(table_b)

# Přidání tabulek do druhého PDF dokumentu
elements_b = []
for table_b in tables_b:
    elements_b.append(table_b)
doc_b.build(elements_b)

print("PDF soubory byly úspěšně vytvořeny.")
# - file log (datetime + error?)

# Odeslání reportů na email

# - file log (datetime + error?)
