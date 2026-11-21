# Liste des chambres
rooms = {
    101: {"price": 120, "available": True},
    102: {"price": 150, "available": True},
    103: {"price": 200, "available": True}
}

# 1. Vérifier la disponibilité
def is_available(room_number):
    if room_number not in rooms:
        raise ValueError("Chambre inexistante")

    return rooms[room_number]["available"]


# 2. Réserver une chambre
def book_room(room_number):
    if room_number not in rooms:
        raise ValueError("Chambre inexistante")

    if not rooms[room_number]["available"]:
        raise ValueError("Chambre déjà réservée")

    rooms[room_number]["available"] = False
    return True


# 3. Annuler une réservation
def cancel_booking(room_number):
    if room_number not in rooms:
        raise ValueError("Chambre inexistante")

    if rooms[room_number]["available"]:
        raise ValueError("Aucune réservation à annuler")

    rooms[room_number]["available"] = True
    return True


# 4. Calculer le prix du séjour
def calculate_price(room_number, nights):
    if room_number not in rooms:
        raise ValueError("Chambre inexistante")

    if nights <= 0:
        raise ValueError("Nombre de nuits invalide")

    return rooms[room_number]["price"] * nights
