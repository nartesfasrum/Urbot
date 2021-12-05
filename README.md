# Urbot

An Urbit-Matrix bridge.

Does not currently work.

Note that this software is currently under development, and I am not responsible for any loss of confidentiality, availability, or integrity of data resulting from use of this software.

## Milestones

* ~~relay text messages from a Matrix room to an Urbit chat~~ **COMPLETE**
* relay text messages from an Urbit chat to a Matrix room
* autojoin/autoconfig Matrix rooms when bot is invited
* relay image messages from an Urbit chat to Matrix
* ~~relay image messages from Matrix to an Urbit chat~~ **COMPLETE**
* provide configuration for displaying of reactions, replies, read receipts, typing notifications from Matrix to Urbit
* provide commands for viewing Matrix room & user metadata

## Requirements

* Quinnat
* matrix-nio
* Boto3
* an Urbit identity
* an Urbit-compatible S3 bucket

## Setup

Install Quinnat via `pip`:

`pip3 install quinnat`

Install matrix-nio via `pip`:

`pip3 install matrix-nio`

Install boto3 via `pip`:

`pip3 install boto3`

Set up a group on your Urbit for your bridge to reside in.

Copy `config.json.example` to `config.json`, and modify it as appropriate to meet your needs.

Start the bridge:

`python3 main.py`
