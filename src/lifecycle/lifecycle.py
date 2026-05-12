#!/usr/bin/python3
#Exemple de script lifecycle
import sys
# Import librairie
sys.path.append('../lib')
import backend_utils as u




def main():
    # lecture json sur l'entree standart
    content=u.readjsoninput()
    #retour de l'execution au daemon
    return print(u.returncode(0,'lifecycle.py'))

if __name__ == '__main__':
    main()