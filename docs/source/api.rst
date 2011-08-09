================
API
================

Kard
==============

.. autoclass:: kardboard.models.Kard
    :members: key, title, backlog_date, start_date, done_date, category, state, priority, cycle_time, lead_time, current_cycle_time, in_progress, backlogged, ticket_system, ticket_system_data

.. autoclass:: kardboard.models.KardQuerySet
    :inherited-members:

Ticket Helpers
=================

.. autoclass:: kardboard.tickethelpers.TicketHelper
    :inherited-members:

.. autoclass:: kardboard.tickethelpers.JIRAHelper
    :inherited-members: