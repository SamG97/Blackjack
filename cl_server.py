from card_game import *
from socket import *
import threading
import random
import time

VERSION = "1.3"
NUMBER_OF_DECKS = 6
STARTING_MONEY = 1000
MINIMUM_BET = 25
WAIT_TIME = 10
RUN = True
EXIT = True
PLAYERS = {}
CURRENT_PLAYERS = []
PLAYER_BUFFER = {}
DECK = Deck(NUMBER_OF_DECKS)
PORTS_IN_USE = [2999]
NEW_GAME_RESPONSES = []
HIT_RESPONSES = []


def get_details(port, address):
    """Gets the details of the player and loads this into a buffer ready for
    the next game
    """

    global PLAYER_BUFFER
    try:
        port = int(port)
        connect_sock = socket()
        addr = (address, port)
        connect_sock.connect(addr)
        client_version = connect_sock.recv(2048)
        if client_version == VERSION:
            existing_player = False
            for player in PLAYERS:
                if PLAYERS[player].address == address:
                    PLAYERS[player].port = port
                    PLAYER_BUFFER[player] = PLAYERS[player]
                    existing_player = True
                    connect_sock.send("found")
                    print "Existing player %s connected on IP address %s " \
                          "and port %d" % (player, address, port)
                    break
            if not existing_player:
                connect_sock.send("new")
                time.sleep(0.1)
                name = connect_sock.recv(2048)
                print "New player %s connected on IP address %s and port %d" \
                      % (name, address, port)
                add_player(name, address, port)
                PLAYER_BUFFER[name] = PLAYERS[name]
                save_players()

        else:
            connect_sock.send("old")
        connect_sock.close()
    except:
        pass


def setup_connection():
    """Listens for new connections and then gives them a unique port in order
    to communicate on
    """

    connect_sock = socket()
    connect_sock.bind((gethostname(), 2999))
    while True:
        try:
            connect_sock.listen(5)
            receive_sock, addr = connect_sock.accept()
            port = 2999
            while port in PORTS_IN_USE:
                port = str(random.randint(3000, 3999))
            PORTS_IN_USE.append(int(port))
            receive_sock.send(port)
            test_port = receive_sock.recv(2048)
            if port == test_port:
                receive_sock.send(str(True))
            else:
                receive_sock.send(str(False))
            receive_sock.close()
            conn = threading.Thread(target=get_details, args=(port, addr[0]))
            conn.daemon = True
            conn.start()
        except:
            pass
    else:
        connect_sock.close()


def get_dealer_choice(hand):
    """Decides if dealer should hit or stand"""

    if hand.evaluate() < 17:
        return "H"
    else:
        return "S"


def clear_responses():
    """Resets the responses list"""

    for i in range(len(NEW_GAME_RESPONSES)):
        NEW_GAME_RESPONSES.pop()


def import_players():
    """Imports stored data on players from a stored file"""

    try:
        for line in open(r"Players.csv"):
            data = line.strip().split(",")
            PLAYERS[data[0]] = Player(data[1], data[2], data[3], data[4],
                                      data[5])
    except IOError:
        pass


def save_players():
    """Updates saved data on players"""

    with open(r"Players.csv", "w") as f:
        for player in PLAYERS:
            line = player + "," + str(PLAYERS[player].balance) + "," \
                   + PLAYERS[player].address + "," \
                   + str(PLAYERS[player].port) \
                   + "," + str(PLAYERS[player].win) + "," \
                   + str(PLAYERS[player].loss) + "\n"
            f.write(line)


def add_player(name, address, port):
    """Creates a new player"""

    PLAYERS[name] = Player(STARTING_MONEY, address, port, 0, 0)


def get_continue_decision(index, address, port):
    """Finds out if a player wants to play the next game"""

    try:
        start_time = time.time()
        connect_sock = socket()
        connect_sock.connect((address, port))
        connect_sock.send("NG")
        response = connect_sock.recv(2048)
        end_time = time.time()
        if end_time - start_time < WAIT_TIME:
            NEW_GAME_RESPONSES[index] = response
    except:
        pass


def join_game():
    """Allows players to join the game"""

    global CURRENT_PLAYERS
    global PLAYER_BUFFER

    clear_responses()

    for i, player in enumerate(CURRENT_PLAYERS):
        NEW_GAME_RESPONSES.append("N")
        response_thread = threading.Thread(target=get_continue_decision,
                                           args=(i, player[1].address,
                                                 player[1].port))
        response_thread.daemon = True
        response_thread.start()

    time.sleep(WAIT_TIME + 1)

    TEMP_PLAYERS = []
    for i, response in enumerate(NEW_GAME_RESPONSES):
        if response == "Y":
            TEMP_PLAYERS.append(CURRENT_PLAYERS[i])
        else:
            PORTS_IN_USE.remove(CURRENT_PLAYERS[i][1].port)

    CURRENT_PLAYERS = TEMP_PLAYERS

    for player in PLAYER_BUFFER:
        CURRENT_PLAYERS.append([player, PLAYER_BUFFER[player], 0])
        message = "\nWelcome %s to Sam's Blackjack game!" % (player)
        display_message(PLAYER_BUFFER[player].address,
                        PLAYER_BUFFER[player].port, message)

    PLAYER_BUFFER = {}


def display_message(address, port, message, mode="D"):
    """Displays a message to a user"""

    try:
        connect_sock = socket()
        connect_sock.connect((address, port))
        connect_sock.send(mode)
        time.sleep(0.1)
        connect_sock.send(message)
        connect_sock.close()
    except:
        pass


def display_message_to_all(message):
    """Displays a message to all connected players"""

    print message
    for player in CURRENT_PLAYERS:
        display_message(player[1].address, player[1].port, message)


def get_bet(index, address, port):
    """Finds out how much a player wants to bet"""

    try:
        start_time = time.time()
        connect_sock = socket()
        connect_sock.connect((address, port))
        connect_sock.send("B")

        bet = 0
        player = CURRENT_PLAYERS[index]
        valid_bet = False
        while not valid_bet:
            try:
                bet = float(connect_sock.recv(2048))
                if bet < MINIMUM_BET:
                    error = "You must bet at least $%f" % (MINIMUM_BET)
                    connect_sock.send(error)
                elif bet > PLAYERS[player[0]].balance:
                    error = "You cannot bet more than your current balance" \
                            "($%.2f)" % (MINIMUM_BET)
                    connect_sock.send(error)
                elif len(str(bet).rstrip("0").split(".")[1]) > 2:
                    error = "You cannot bet in denominations of less than a " \
                            "cent"
                    connect_sock.send(error)
                else:
                    valid_bet = True
            except ValueError:
                connect_sock.send("You must enter your bet in digits")
        connect_sock.send("Accept")

        PLAYERS[player[0]].balance -= bet
        CURRENT_PLAYERS[index][2] = bet

        end_time = time.time()
        if end_time - start_time < WAIT_TIME:
            NEW_GAME_RESPONSES[index] = response
    except:
        pass


def bets():
    """Allows users to make bets"""

    # Gets bets
    for i, player in enumerate(CURRENT_PLAYERS):
        bet = threading.Thread(target=get_bet, args=(i, player[1].address,
                                                     player[1].port))
        bet.daemon = True
        bet.start()

    time.sleep(WAIT_TIME + 1)

    # Displays bets
    display_message_to_all("")
    for player in CURRENT_PLAYERS:
        if player[2] == 0:
            player[2] = MINIMUM_BET

        if player[1].balance == 0:
            message = "%s is going all in ($%.2f)!" % (player[0], player[2])
        else:
            message = "%s is betting $%.2f" % (player[0], player[2])
        display_message_to_all(message)
    display_message_to_all("")


def get_player_hit_choice(index, player):
    """Asks player if they want to hit or stand"""

    try:
        start_time = time.time()
        connect_sock = socket()
        connect_sock.connect((player.address, player.port))
        connect_sock.send("HS")
        choice = None
        while choice not in ["H", "S"]:
            choice = connect_sock.recv(2048)
            if choice not in ["H", "S"]:
                connect_sock.send("Fail")
            else:
                connect_sock.send("Accept")
        end_time = time.time()
        if end_time - start_time < WAIT_TIME:
            HIT_RESPONSES[index] = choice
    except:
        pass


def bankrupt(player):
    """Deletes a bankrupt player"""

    global PLAYERS
    del PLAYERS[player[0]]

    message = "You are now bankrupt and will be kicked, you can rejoin " \
              "as a new player"
    display_message(player[1].address, player[1].port, message, mode="S")

def game():
    """Runs the actual game"""

    # Displays stats on players currently in the game before it starts
    print "\nStarting new game..."
    header = "\n" + "PLAYER STATS".center(25, "-") + "\n"
    display_message_to_all(header)
    for player in CURRENT_PLAYERS:
        if player[1].win + player[1].loss == 0:
            win_percentage = 0
        else:
            win_percentage = float(player[1].win) / \
                               (player[1].win + player[1].loss) * 100
        message = player[0].center(25, "-") + "\n" \
            + ("Balance: $%.2f" % (player[1].balance)).center(25) + "\n" \
            + ("Wins: %.3d" % (player[1].win)).center(25) + "\n" \
            + ("Losses: %.3d" % (player[1].loss)).center(25) + "\n" \
            + ("Win Percentage: %.2f%%" % (win_percentage)).center(25) \
            + "\n"
        display_message_to_all(message)

    # Set up game round
    print "Getting bets..."
    bets()
    dealer_hand = Hand()
    dealer_hand.draw(DECK)
    message = "Dealer's first card is " + str(dealer_hand[0]) + "\n"
    display_message_to_all(message)
    player_hands = []
    global HIT_RESPONSES
    HIT_RESPONSES = []
    for player in CURRENT_PLAYERS:
        player_hands.append(Hand())
        HIT_RESPONSES.append("H")
    for player_hand in player_hands:
        player_hand.draw(DECK)

    # Get choices while at least one play is still hitting
    while "H" in HIT_RESPONSES:
        # Display each player's hand
        for i, player_hand in enumerate(player_hands):
            if HIT_RESPONSES[i] == "H" and player_hand.evaluate() <= 21:
                player_hand.draw(DECK)
            message = "%s's hand: " % (CURRENT_PLAYERS[i][0]) \
                      + str(player_hand)
            display_message_to_all(message)

        # Get player choices
        for i, player_hand in enumerate(player_hands):
            if player_hand.evaluate() > 21:
                message = "You are bust! Waiting for other players..."
                display_message(CURRENT_PLAYERS[i][1].address,
                                CURRENT_PLAYERS[i][1].port,
                                message)
                HIT_RESPONSES[i] = "S"
            elif HIT_RESPONSES[i] == "H":
                HIT_RESPONSES[i] = "S"
                response = threading.Thread(target=get_player_hit_choice,
                                            args=(i, CURRENT_PLAYERS[i][1]))
                response.daemon = True
                response.start()
            else:
                display_message(CURRENT_PLAYERS[i][1].address,
                                CURRENT_PLAYERS[i][1].port,
                                "Waiting for other players...")

        time.sleep(WAIT_TIME + 1)

        # Display player choices
        display_message_to_all("")
        for i, player_hand in enumerate(player_hands):
            if player_hand.evaluate() > 21:
                message = "%s is bust!" % (CURRENT_PLAYERS[i][0])
            elif HIT_RESPONSES[i] == "H":
                message = "%s is hitting!" % (CURRENT_PLAYERS[i][0])
            else:
                message = "%s is standing!" % (CURRENT_PLAYERS[i][0])
            display_message_to_all(message)

    # Display final hands
    display_message_to_all("")
    for i, player_hand in enumerate(player_hands):
        message = "%s's final hand: " % (CURRENT_PLAYERS[i][0]) \
                  + str(player_hand)
        display_message_to_all(message)

    # Get dealer hand
    display_message_to_all("")
    while get_dealer_choice(dealer_hand) == "H":
        dealer_hand.draw(DECK)

    display_message_to_all("Dealer's hand: " + str(dealer_hand) + "\n")

    # Evaluate player win / loss and update player stats
    current_time = time.localtime()
    time_name = "%04d%02d%02d%02d%02d%02d" % (current_time.tm_year,
                                              current_time.tm_mon,
                                              current_time.tm_mday,
                                              current_time.tm_hour,
                                              current_time.tm_min,
                                              current_time.tm_sec)
    filename = r"Logs\\" + time_name + ".csv"
    with open(filename, "w") as f:
        for i, player_hand in enumerate(player_hands):
            address = CURRENT_PLAYERS[i][1].address
            port = CURRENT_PLAYERS[i][1].port
            balance = CURRENT_PLAYERS[i][1].balance
            if player_hand.evaluate() > 21:
                message = "Player is bust! %s loses!" % (CURRENT_PLAYERS[i][0])
                PLAYERS[CURRENT_PLAYERS[i][0]].loss += 1
                log_message = "%s,%s,%d,%d,%d,0,PB\n" % (CURRENT_PLAYERS[i][0],
                                                         address, port,
                                                         balance,
                                                         CURRENT_PLAYERS[i][2])
            elif dealer_hand.evaluate() > 21:
                message = "Dealer is bust! %s wins!" % (CURRENT_PLAYERS[i][0])
                PLAYERS[CURRENT_PLAYERS[i][0]].win += 1
                PLAYERS[CURRENT_PLAYERS[i][0]].balance += \
                    CURRENT_PLAYERS[i][2] * 2.5
                log_message = "%s,%s,%d,%d,%d,1,DB\n" % (CURRENT_PLAYERS[i][0],
                                                         address, port,
                                                         balance,
                                                         CURRENT_PLAYERS[i][2])
            elif player_hand.evaluate() > dealer_hand.evaluate():
                message = "%d > %d! %s wins!" % \
                      (player_hand.evaluate(), dealer_hand.evaluate(),
                       CURRENT_PLAYERS[i][0])
                PLAYERS[CURRENT_PLAYERS[i][0]].win += 1
                PLAYERS[CURRENT_PLAYERS[i][0]].balance += \
                    CURRENT_PLAYERS[i][2] * 2.5
                log_message = "%s,%s,%d,%d,%d,1,PW\n" % (CURRENT_PLAYERS[i][0],
                                                         address, port,
                                                         balance,
                                                         CURRENT_PLAYERS[i][2])
            else:
                message = "%d <= %d! %s loses!" % \
                      (player_hand.evaluate(), dealer_hand.evaluate(),
                       CURRENT_PLAYERS[i][0])
                PLAYERS[CURRENT_PLAYERS[i][0]].loss += 1
                log_message = "%s,%s,%d,%d,%d,0,DW\n" % (CURRENT_PLAYERS[i][0],
                                                         address, port,
                                                         balance,
                                                         CURRENT_PLAYERS[i][2])
            display_message_to_all(message)
            f.write(log_message)
            if CURRENT_PLAYERS[i][1].balance < MINIMUM_BET:
                message = "%s is bankrupt and their profile will now " \
                          "be deleted" % (CURRENT_PLAYERS[i][0])
                display_message_to_all(message)
                bankrupt(CURRENT_PLAYERS[i])
                

    # Return cards to the deck
    for player_hand in player_hands:
        player_hand.clear(DECK)
    dealer_hand.clear(DECK)


def shutdown():
    """Sends a shutdown signal to clients"""

    message = "Server is shutting down"
    print message
    for player in CURRENT_PLAYERS:
        display_message(player[1].address, player[1].port, message, mode="S")


def main():
    """Runs the main function in a separate thread"""

    global EXIT
    while RUN:
        print "Shuffling deck..."
        DECK.shuffle()  # Shuffles deck to prevent repetition
        for i in range(NUMBER_OF_DECKS * 2):
            join_game()
            if len(CURRENT_PLAYERS) > 0:
                game()
                save_players()
            else:
                print "Not enough players to start game"
            if not RUN:
                break
    EXIT = False


if __name__ == "__main__":
    import_players()
    listener = threading.Thread(target=setup_connection)
    listener.daemon = True
    listener.start()

    main_game = threading.Thread(target=main)
    main_game.daemon = True
    main_game.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        try:
            RUN = False
            print "CTRL + C again to force shutdown the server"
            while EXIT:
                pass
            print "Shutdown"
        except KeyboardInterrupt:
            print "Immediately shuting down server..."
        shutdown()
