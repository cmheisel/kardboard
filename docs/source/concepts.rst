Kanban concepts
================

**kardboard** is meant to represent physical cards on a Kanban board. To understand the application it's useful to have some background on Kanban concepts.

Card
    A card represents a unit of work, it's the central object around which almost everything else revolves. Ultimatley it represents some piece of business value.

Ticket
    For kardboard's purposes a ticket is an item contained in a seperate system, that has additional data about a particular card. For example, a Card in kardboard may know when a card was backlogged, started and completed but its Ticket would know who it's assigned to currently. A Card and a Ticket are linked together via the Card's **key** value.

Backlog
    A card that is still in a planning, or Todo state. Backlog is one of three core states a card can be in.

In progress / work in progress
    Cards that moved from the backlog to being actively worked on by someone. Typically "In progress" covers many sub-states in a teams workflow.

Done
    Cards for whom the value has been delivered, by whatever criteria the team uses. For software development teams it could mean the software was deployed, or signed off on and is ready for release, etc.

Lead time
    A measurement, in number of business days, between the date a card enters the Backlog and the date the card is Done. This a measure of the time it takes from "we decided to do a thing" to "the thing we decided to do is done." Think about rides at Disney World. Lead time is a measurement of how long it takes from you waiting in line till the time you step off the ride.

Cycle time
    A measurement, in number of business days, between the date a card enters In progress to the date the card is Done. This is a measure of time it takes from "we started doing a thing" to "the thing is done.". Think about rides at Disney World. Cycle time is a measurement of how long it takes from when you get on the ride to when you get off.

Throughput
    The number of cards that can be completed in a given time frame. The lower the cycle time, the higher the throughput. In Disney World terms, it's riders-per-hour.