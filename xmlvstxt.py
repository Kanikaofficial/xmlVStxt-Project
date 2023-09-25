import os
from bs4 import BeautifulSoup
from difflib import get_close_matches
from collections import Counter
import pandas as pd


def compare_first_headers_with_xml(txt_file, xml_file, output_file):
    with open(txt_file, 'r', encoding='utf-8') as f:
        txt_data = f.readlines()

    first_headers = [line.split('#@#')[0].strip() for line in txt_data]
    total_headers = len(first_headers)
    header_locations = {header: position + 1 for position, header in enumerate(first_headers)}
    duplicate_headers = [header for header, count in Counter(first_headers).items() if count > 1]
    duplicate_header_locations = [idx for header, idx in header_locations.items() if header in duplicate_headers]

    try:
        with open(xml_file, 'r', encoding='utf-8') as xml_file:
            xml_content = xml_file.read()
            soup = BeautifulSoup(xml_content, 'xml')
    except Exception as e:
        print(f"Error while parsing the XML file: {e}")
        return []

    xml_headers = {nav_point['label']: nav_point['label'] for nav_point in soup.find_all('navPoint')}

    updated_txt_data = []
    for line in txt_data:
        header = line.split('#@#')[0].strip()
        if header not in xml_headers.values():
            close_match = get_close_matches(header, xml_headers.values(), n=1, cutoff=0.5)
            if close_match:
                line = line.replace(header, close_match[0])
        updated_txt_data.append(line)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(updated_txt_data)

    missing_headers = [header for header in first_headers if header not in xml_headers.values()]
    missing_header_locations = [header_locations[header] for header in missing_headers]
    return missing_headers, duplicate_headers, missing_header_locations, duplicate_header_locations


def process_asin_files(input_folder_path, output_folder_path):
    os.makedirs(output_folder_path, exist_ok=True)

    asin_txt_files = [file for file in os.listdir(input_folder_path) if file.endswith('.txt')]
    asin_xml_files = [file for file in os.listdir(input_folder_path) if file.endswith('.xml')]

    for txt_file in asin_txt_files:
        asin = os.path.splitext(txt_file)[0]
        xml_file = f"{asin}.xml"

        if xml_file in asin_xml_files:
            txt_file_path = os.path.join(input_folder_path, txt_file)
            xml_file_path = os.path.join(input_folder_path, xml_file)
            output_file_path = os.path.join(output_folder_path, f"{asin}_output.txt")

            missing_headers, duplicate_headers, missing_header_locations, duplicate_header_locations = compare_first_headers_with_xml(txt_file_path, xml_file_path, output_file_path)

            if missing_headers or duplicate_headers:
                print(f"Processing ASIN: {asin}")
                if missing_headers:
                    print(f"Missing headers for ASIN: {asin}")
                    for header, location in zip(missing_headers, missing_header_locations):
                        print(f"Header: {header}, Location: Line {location + 1}")

                if duplicate_headers:
                    print(f"Duplicate headers for ASIN: {asin}")
                    for header, location in zip(duplicate_headers, duplicate_header_locations):
                        print(f"Header: {header}, Location: Line {location + 1}")

                if len(duplicate_headers) < len(missing_headers):
                    duplicate_headers.extend([''] * (len(missing_headers) - len(duplicate_headers)))
                    duplicate_header_locations.extend([-1] * (len(missing_headers) - len(duplicate_header_locations)))

                df = pd.DataFrame({'Missing Headers': missing_headers,
                                   'Missing Header Locations': missing_header_locations,
                                   'Duplicate Headers': duplicate_headers,
                                   'Duplicate Header Locations': duplicate_header_locations})

                excel_output_file = os.path.join(output_folder_path, f"{asin}_missing_headers.xlsx")
                df.to_excel(excel_output_file, index=False)
            else:
                print(f"All headers from the text file for ASIN {asin} are present in the XML file.")

input_folder_path = input("Enter the path of the input folder: ")
output_folder_path = input("Enter the path of the output folder: ")

process_asin_files(input_folder_path, output_folder_path)