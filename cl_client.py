from socket import *
import threading
import time
import ftplib
import sys
import os

VERSION = "1.3"
SERVER = "STUDENT04"
PORT = 0
WAIT_TIME = 10
RUN = True


def update():
    """Downloads the installer"""

    ftp = ftplib.FTP("192.168.1.106", user="ftpuser", passwd="pass")
    file_writer = open(r"Blackjack.pyc", "wb")
    ftp.retrbinary("RETR Blackjack.pyc", file_writer.write)
    file_writer.close()
    ftp.quit()
    print "Your client is out of date, restarting to update..."
    python = sys.executable
    os.execl(python, python, * sys.argv)


def create_connection():
    """Creates an initial connection to the server"""

    try:
        print "\nTrying to connect to server..."
        sock = socket()
        sock.connect((gethostbyname(SERVER), 2999))
        port = sock.recv(2048)
        sock.send(port)
        resp = sock.recv(2048)
        sock.close()
        if bool(resp):
            port = int(port)
            connect_sock = socket()
            connect_sock.bind((gethostbyname(SERVER), port))
            connect_sock.listen(5)
            receive_sock, address = connect_sock.accept()
            connect_sock.close()
            receive_sock.send(VERSION)
            known = receive_sock.recv(2048)
            if known == "new":
                name = ""
                print "Existing player profile not found, "\
                      "creating new profile..."
                while len(name) not in range(1, 21):
                    prompt = "Please enter your name "\
                             "(this cannot be changed): "
                    name = raw_input(prompt)
                    if len(name) == 0:
                        print "Please enter a name"
                    elif len(name) > 20:
                        print "The maximum length for a name is 20 characters"
                receive_sock.send(name)
            elif known == "found":
                print "Loading player profile..."
            else:
                update()
                return False
            receive_sock.close()

            print "Waiting for next game to start..."

            return port
        else:
            return False
    except:
        print "Cannot connect to server"


def new_game(sock, placeholder):
    """Asks if the player wants to join the next game"""

    start_time = time.time()
    choice = ""
    while choice not in ["Y", "N"]:
        prompt = "\nWould you like to play another game - " \
                 "(Y)es or (N)o: "
        choice = raw_input(prompt).upper()
    end_time = time.time()
    if end_time - start_time < WAIT_TIME:
        sock.send(choice)
        print "Waiting for other players..."
    else:
        print "Response time out..."
        global RUN
        RUN = False
    sock.close()


def display_message(sock, placeholder):
    """Displays a message from the server"""

    message = sock.recv(2048)
    print message
    sock.close()


def get_hit_choice(sock, placeholder):
    """Gets if the user wants to hit or stick"""

    start_time = time.time()
    response = ""
    while response != "Accept":
        choice = ""
        while choice not in ["H", "S"]:
            choice = raw_input("\n(H)it or (S)tand: ").upper()
        end_time = time.time()
        if end_time - start_time < WAIT_TIME:
            sock.send(choice)
            response = sock.recv(2048)
            if response != "Accept":
                print "An error occured, please try again"
            else:
                print "Waiting for other players..."
        else:
            break
    sock.close()


def get_bet(sock, placeholder):
    """Gets the bet amount"""

    start_time = time.time()
    bet = 0
    response = None
    while response != "Accept":
        bet = raw_input("\nHow much would you like to bet: $")
        end_time = time.time()
        if end_time - start_time < WAIT_TIME:
            sock.send(bet)
            response = sock.recv(2048)
            if response != "Accept":
                print response
            else:
                print "Waiting for other players..."
        else:
            break
    sock.close()


def shutdown(sock, placeholder):
    """Closes the client if the server shuts down"""

    global RUN
    message = sock.recv(2048)
    print message
    sock.close()
    RUN = False


def check_incomming_messages():
    """Interprets incoming communications"""

    operations = {"NG": new_game, "D": display_message,
                  "HS": get_hit_choice, "B": get_bet, "S": shutdown}
    connect_sock = socket()
    connect_sock.bind((gethostbyname(SERVER), PORT))
    while True:
        connect_sock.listen(5)
        receive_sock, address = connect_sock.accept()
        mode = receive_sock.recv(2048)
        try:
            operation = threading.Thread(target=operations[mode],
                                         args=(receive_sock, 0))
            operation.daemon = True
            operation.start()
        except:
            pass
    else:
        connect_sock.close()


if __name__ == "__main__":
    PORT = create_connection()
    if PORT:
        listen = threading.Thread(target=check_incomming_messages)
        listen.daemon = True
        listen.start()

        try:
            while RUN:
                pass
        except KeyboardInterrupt:
            print "Force shutting down"

    print "Exiting in",
    for i in range(3, 0, -1):
        print "%d..." % (i),
        time.sleep(1)
