###
### analyze_pings.py
###

import fileinput
from datetime import datetime
import json

def main():
    """Main body."""

    for line in fileinput.input():
        print line.strip()

if __name__ == '__main__':
    main()
