import os
from dotenv import load_dotenv
import requests
import re
from lxml import etree
import io
from typing import Final
from datetime import datetime

load_dotenv()

QUALYS_USER: Final = os.getenv('QUALYS_USER')
QUALYS_PASS: Final = os.getenv('QUALYS_PASS')
BASE_API_URL: Final = os.getenv('BASE_API_URL')
BASE_ASSET_URL = os.getenv('BASE_ASSET_URL')
HOST_LIST_URL = f'{BASE_API_URL}api/2.0/fo/asset/host/?action=list'
REPORT_LIST_URL = f'{BASE_API_URL}api/2.0/fo/report/?action=list'
REPORT_DOWNLOAD_URL = f'{BASE_API_URL}api/2.0/fo/report/?action=fetch&id='
TOKEN_URL = f'{BASE_ASSET_URL}auth'

SESSION_URL = f'{BASE_API_URL}api/2.0/fo/session/'
SESSION_HEADERS = {
    'X-Requested-With': 'Python',
    'accept': 'application/json',
}

SESSION_DATA = {
    'action': 'login',
    'username': QUALYS_USER,
    'password': QUALYS_PASS,
}

class Report:
    def __init__(self, session, report_path, report_download_url):
        self.session = session
        self.report_path = report_path
        self.report_download_url = report_download_url

    def authenticate(self) -> bool:
        response = self.session.post(SESSION_URL, headers=SESSION_HEADERS, data=SESSION_DATA)
        return response.status_code == 200

    def validate_xml(self, response: requests.Response):
        try:
            root = etree.fromstring(response.content)
            dtd_declaration = re.search(r'<!DOCTYPE.*?>', response.text).group(0)
            if dtd_declaration:
                match = re.search(r'SYSTEM\s+"([^"]+)"', dtd_declaration)
                if match:
                    dtd_url = match.group(1)
                    dtd_response = self.session.get(dtd_url)
                    dtd_content = dtd_response.content
                    dtd = etree.DTD(io.BytesIO(dtd_content))
                    if dtd.validate(root):
                        return root.findall('.//REPORT')
        except Exception as e:
            print(f'Error in XML validation: {e}')
        return False

    def download_report(self, report_id: str, report_file_path: str, output_format: str):
        download_url = f'{self.report_download_url}{report_id}'
        downloaded_report = self.session.get(url=download_url, headers=SESSION_HEADERS)
        with open(report_file_path, 'wb' if output_format == 'PDF' else 'w') as f:
            if output_format == 'PDF':
                f.write(downloaded_report.content)
            else:
                f.write(downloaded_report.text)

    def get_reports(self, valid_reports):
        for report in valid_reports:
            report_id = report.find('ID').text
            title = report.find('TITLE').text.replace('-', '_')
            output_format = report.find('OUTPUT_FORMAT').text
            report_date = report.find('LAUNCH_DATETIME').text[:10]

            report_file = f'Scan_Report_{title}_{report_date}.{output_format.lower()}'.replace(' ', '_')
            report_file_path = os.path.join(self.report_path, report_file)

            self.download_report(report_id, report_file_path, output_format)

def main():
    session = requests.Session()
    today = datetime.now().strftime('%Y_%m_%d')
    report_path = os.path.join(os.getcwd(), today)
    os.makedirs(report_path, exist_ok=True)

    report = Report(session, report_path, REPORT_DOWNLOAD_URL)

    if report.authenticate():
        print('Authentication successful')
        reports = session.get(url=REPORT_LIST_URL, headers=SESSION_HEADERS)
        valid_reports = report.validate_xml(reports)
        if valid_reports:
            print('XML validation successful')
            report.get_reports(valid_reports)
        else:
            print('XML validation failed')
    else:
        print('Authentication failed')



if __name__ == '__main__':
    main()


# import os
# from dotenv import load_dotenv
# import aiohttp
# import asyncio
# import re
# from lxml import etree
# import io
# from typing import Final
# from datetime import datetime

# load_dotenv()

# QUALYS_USER: Final = os.getenv('QUALYS_USER')
# QUALYS_PASS: Final = os.getenv('QUALYS_PASS')
# BASE_API_URL: Final = os.getenv('BASE_API_URL')
# BASE_ASSET_URL: Final = os.getenv('BASE_ASSET_URL')
# HOST_LIST_URL: Final = f'{BASE_API_URL}api/2.0/fo/asset/host/?action=list'
# REPORT_LIST_URL: Final = f'{BASE_API_URL}api/2.0/fo/report/?action=list'
# REPORT_DOWNLOAD_URL: Final = f'{BASE_API_URL}api/2.0/fo/report/?action=fetch&id='
# TOKEN_URL: Final = f'{BASE_ASSET_URL}auth'

# SESSION_URL: Final = f'{BASE_API_URL}api/2.0/fo/session/'
# SESSION_HEADERS: Final = {
#     'X-Requested-With': 'Python',
#     'accept': 'application/json',
# }

# SESSION_DATA: Final = {
#     'action': 'login',
#     'username': QUALYS_USER,
#     'password': QUALYS_PASS,
# }

# class Report:
#     def __init__(self, report_path: str, report_download_url: str):
#         self.report_path = report_path
#         self.report_download_url = report_download_url
#         self.session = None

#     async def __aenter__(self):
#         self.session = aiohttp.ClientSession()
#         return self

#     async def __aexit__(self, exc_type, exc_value, traceback):
#         await self.session.close()

#     async def authenticate(self) -> bool:
#         async with self.session.post(SESSION_URL, headers=SESSION_HEADERS, data=SESSION_DATA) as response:
#             print(f'Authentication response status: {response.status}')
#             return response.status == 200

#     async def validate_xml(self, response: aiohttp.ClientResponse):
#         try:
#             content = await response.text()
#             print(f'XML Response Content: {content[:500]}')  # Print the first 500 characters of the XML response for debugging
#             root = etree.fromstring(content.encode('utf-8'))
#             dtd_declaration = re.search(r'<!DOCTYPE.*?>', content)
#             if dtd_declaration:
#                 dtd_declaration = dtd_declaration.group(0)
#                 match = re.search(r'SYSTEM\s+"([^"]+)"', dtd_declaration)
#                 if match:
#                     dtd_url = match.group(1)
#                     async with self.session.get(dtd_url) as dtd_response:
#                         dtd_content = await dtd_response.read()
#                         dtd = etree.DTD(io.BytesIO(dtd_content))
#                         if dtd.validate(root):
#                             return root.findall('.//REPORT')
#                         else:
#                             print('DTD validation failed')
#             else:
#                 print('DTD declaration not found')
#         except Exception as e:
#             print(f'Error in XML validation: {e}')
#         return False

#     async def download_report(self, report_id: str, report_file_path: str, output_format: str):
#         download_url = f'{self.report_download_url}{report_id}'
#         async with self.session.get(download_url, headers=SESSION_HEADERS) as response:
#             if output_format == 'PDF':
#                 content = await response.read()
#                 with open(report_file_path, 'wb') as f:
#                     f.write(content)
#             else:
#                 content = await response.text()
#                 with open(report_file_path, 'w') as f:
#                     f.write(content)

#     async def get_reports(self, valid_reports):
#         tasks = []
#         for report in valid_reports:
#             report_id = report.find('ID').text
#             title = report.find('TITLE').text.replace('-', '_')
#             output_format = report.find('OUTPUT_FORMAT').text
#             report_date = report.find('LAUNCH_DATETIME').text[:10]

#             report_file = f'Scan_Report_{title}_{report_date}.{output_format.lower()}'.replace(' ', '_')
#             report_file_path = os.path.join(self.report_path, report_file)

#             tasks.append(self.download_report(report_id, report_file_path, output_format))
        
#         await asyncio.gather(*tasks)

# async def main():
#     today = datetime.now().strftime('%Y_%m_%d')
#     report_path = os.path.join(os.getcwd(), today)
#     os.makedirs(report_path, exist_ok=True)

#     async with Report(report_path, REPORT_DOWNLOAD_URL) as report:
#         if await report.authenticate():
#             print('Authentication successful')
#             async with report.session.get(REPORT_LIST_URL, headers=SESSION_HEADERS) as reports_response:
#                 print(f'Get Reports response status: {reports_response.status}')
#                 valid_reports = await report.validate_xml(reports_response)
#                 if valid_reports:
#                     print('XML validation successful')
#                     await report.get_reports(valid_reports)
#                 else:
#                     print('XML validation failed')
#         else:
#             print('Authentication failed')

# if __name__ == '__main__':
#     asyncio.run(main())
