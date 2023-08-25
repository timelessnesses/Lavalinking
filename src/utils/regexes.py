import re

REGEX_DETECT_URL = r"(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-&?=%.]+"

def detect_url(url: str) -> bool:
    return len(re.findall(REGEX_DETECT_URL, url)) != 0