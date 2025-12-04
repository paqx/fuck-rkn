import json
import csv
import os
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
HAR_FILES_PATH = os.path.join(SCRIPT_DIR, '../../etc/har/')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, '../../etc/har/')


def get_files_by_extension(dir, ext):
    files = []
    for file in os.listdir(dir):
        if file.endswith(ext):
            files.append(os.path.join(dir, file))
    return files


def main():
    files = get_files_by_extension(HAR_FILES_PATH, '.har')
    unique_ips = {}

    for file in files:
        with open(file, 'r', encoding='utf-8') as fin:
            har_data = json.load(fin)

        entries = har_data['log']['entries']
        output_path = os.path.join(OUTPUT_DIR, Path(file).stem)

        with open(f"{output_path}.csv", 'w', encoding='utf-8') as fout_csv:
            writer = csv.writer(fout_csv)
            writer.writerow([
                'url',
                'ip',
                'method',
                'status'
            ])

            for entry in entries:
                url = entry['request']['url']
                ip = entry.get('serverIPAddress', 'N/A')
                method = entry['request']['method']
                status = entry['response']['status']

                if status >= 400:
                    continue

                writer.writerow([
                    url,
                    ip,
                    method,
                    status
                ])

                if ip and ip not in unique_ips:
                    unique_ips[ip] = url

        with open(f"{output_path}.json", 'w', encoding='utf-8') as fout_json:
            json.dump(unique_ips, fout_json, indent=2)


if __name__ == "__main__":
    main()
