#!/usr/bin/python3

import sys

sys.path.append('../lib')
import backend_utils as u




def main():
    content=u.readjsoninput()
    return print(u.returncode(0,'lifecycle.py'))

if __name__ == '__main__':
    main()