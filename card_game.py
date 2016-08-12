import random


class Card():
    """Stores the data on a single card"""

    def __init__(self, value, suit):
        """Creates a new instance of a card object"""

        self.value = value
        self.suit = suit

    def __str__(self):
        """Formats the card into a human readable form"""

        alt_names = {1: "Ace", 11: "Jack", 12: "Queen", 13: "King"}
        name = self.value
        if name in alt_names:
            name = alt_names[name]
        else:
            name = str(name)
        return "%s of %s" % (name, self.suit)


class CardContainer():
    """Provides a container for storing cards in a deck or hand"""

    cards = []  # Stores the cards in the container

    def __init__(self):
        """This class should never be declared on its own so has no __init__"""
        pass

    def __len__(self):
        """Returns the number of cards in the deck"""

        return len(self.cards)

    def __getitem__(self, index):
        """Returns the card at a given index"""

        return self.cards[index]

    def __iter__(self):
        """Returns the deck in its current order"""

        for card in self.cards:
            yield card

    def __str__(self):
        """Formats the cards into a human readable form
           Displays in the form of a list
        """

        print_string = "["
        for card in self.cards:
            print_string += card.__str__()
            print_string += ", "
        if len(self.cards) > 0:
            print_string = print_string[:-2] + "]"
        else:
            print_string += "]"
        return print_string

    def make_list(self):
        return_list = []
        for card in self.cards:
            return_list.append(str(card))
        return return_list


class Deck(CardContainer):
    """Stores the data for a deck"""

    def __init__(self, number_of_decks):
        """Creates a new instance of a deck object"""

        suits = ("Spades", "Clubs", "Hearts", "Diamonds")
        for deck in range(number_of_decks):  # Allows multiple decks to be used
            for suit in suits:
                for card in range(1, 14):
                    self.cards.append(Card(card, suit))

    def deal_card(self):
        """'Deals' the top card in the deck"""

        return self.cards.pop(0)

    def return_card(self, returned_card):
        """Returns a card to the back of the deck"""

        self.cards.append(returned_card)

    def shuffle(self):
        """Shuffles the deck into a random order"""

        if len(self.cards) > 1:
            for i in range(10000 * (len(self.cards) // 52 + 1)):
                pos_1 = random.randint(0, len(self.cards) - 1)
                pos_2 = pos_1
                while pos_2 == pos_1:
                    pos_2 = random.randint(0, len(self.cards) - 1)
                self.cards[pos_1], self.cards[pos_2] = \
                    self.cards[pos_2], self.cards[pos_1]


class Hand(CardContainer):
    """Stores the data for a player's hand"""

    def __init__(self):
        """Creates a new instance of a deck object"""

        self.cards = []

    def draw(self, source):
        """Draws a card from a source deck"""

        self.cards.append(source.deal_card())

    def clear(self, destination):
        """Returns cards in a hand to a deck"""

        for card in self.cards:
            destination.return_card(card)

    def evaluate(self):
        """Finds the highest current value of the hand without going bust,
        if possible
        """

        total = 0
        number_of_aces = 0
        for card in self.cards:
            if card.value == 1:
                number_of_aces += 1
                total += 11
            elif card.value > 10:
                total += 10
            else:
                total += card.value

            if total > 21 and number_of_aces > 0:
                number_of_aces -= 1
                total -= 10
        return total


class Player():
    """Stores data about a player"""

    def __init__(self, balance, address, port, win, loss):
        self.balance = float(balance)
        self.address = address
        self.port = int(port)
        self.win = int(win)
        self.loss = int(loss)


if __name__ == "__main__":
    deck = Deck(1)
    print "'deck' has been created for testing; it is a single Deck"
