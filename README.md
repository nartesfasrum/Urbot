# Urbot

An Urbit-Matrix bridge.

Does not currently work.

Note that this software is currently under development, and I am not responsible for any loss of confidentiality, availability, or integrity of data resulting from use of this software.

## Milestones

* ~~relay text messages from a Matrix room to an Urbit chat~~ **COMPLETE** [you are here]
* relay text messages from a Matrix room to an Urbit chat
* autojoin/autoconfig Matrix rooms when bot is invited
* relay image messages from an Urbit chat to Matrix
* relay image messages from Matrix to an Urbit chat
* provide configuration for displaying of reactions, replies, read receipts, typing notifications from Matrix to Urbit
* provide commands for viewing Matrix room & user metadata

## Requirements

* Quinnat
* matrix-nio
* an Urbit identity

## Setup

Install Quinnat via `pip`:

`pip3 install quinnat`

Install matrix-nio via `pip`:

`pip3 install matrix-nio`

Set up a group on your Urbit for your bridge to reside in.

Copy `example.ini` to `default.ini`, and modify it as appropriate to meet your needs.

Start the bridge:

`python3 main.py`
