# Urbot

An Urbit-Matrix bridge.

Note that this software is currently under development, and I am not responsible for any loss of confidentiality, availability, or integrity of data resulting from use of this software.

## Milestones

* ~~relay text messages from a Matrix room to an Urbit chat~~ **COMPLETE**
* relay text messages from an Urbit chat to a Matrix room
* ~~autojoin~~/autoconfig Matrix rooms when bot is invited **SEMI-COMPLETE**
* ~~relay media messages from Matrix to an Urbit chat~~ **COMPLETE**
* relay media messages from an Urbit chat to a Matrix room
* provide configuration for displaying of reactions, replies, read receipts, typing notifications from Matrix to Urbit
* provide commands for viewing Matrix room & user metadata

## Requirements

* an Urbit identity
* an Urbit-compatible S3 bucket
* matrix-nio
* Quinnat

## Setup

Install required dependencies:

`pip3 install -r requirements.txt`

Set up a group on your Urbit for your bridge to reside in.

Copy `config.json.example` to `config.json`, and modify it as appropriate to meet your needs.

Start the bridge:

`python3 main.py`

Note that if it has been some time since the Urbit channels you are bridging have received messages, it may take some time for your bridged messages to appear on the Urbit side. This is expected; remain Calm TM and Give It A Minute.
