import os
import gzip
import re
from collections import defaultdict


def log_file_lines(directory):
    sorted_files = sorted(os.listdir(directory))
    for filename in sorted_files:
        if filename.endswith('.log') or filename.endswith('.log.gz'):
            date_str = filename.split('-')[0:3]
            date_str = '-'.join(date_str)
            if filename.endswith('.log'):
                with open(os.path.join(directory, filename), 'r', encoding='utf-8') as f:
                    for line in f.readlines():
                        yield date_str, line
            elif filename.endswith('.log.gz'):
                with gzip.open(os.path.join(directory, filename), 'rt', encoding='utf-8') as f:
                    for line in f.readlines():
                        yield date_str, line


IP_PATTERN = re.compile(
    r'\[(\d{2}:\d{2}:\d{2})\] \[Server thread/INFO\]: (.+)\[/(.+):\d+\] logged in')


def extract_ip_and_user(lines, ip_to_usernames):
    for date_str, line in lines:
        ip_match = IP_PATTERN.search(line)
        if ip_match:
            username = ip_match.group(2)
            ip_address = ip_match.group(3)
            ip_to_usernames[ip_address].add(username)


def find_shared_ips(ip_to_usernames):
    for ip, usernames in ip_to_usernames.items():
        if len(usernames) > 1:
            print(f"IP: {ip}, Usernames: {', '.join(usernames)}")


def main():
    ip_to_usernames = defaultdict(set)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    lines = log_file_lines(os.path.join(base_dir, "..", 'logs'))

    extract_ip_and_user(lines, ip_to_usernames)
    find_shared_ips(ip_to_usernames)


if __name__ == '__main__':
    main()
