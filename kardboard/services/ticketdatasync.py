def set_due_date_from_ticket(kard, ticket):
    kard.due_date = ticket.get('due_date', None)
