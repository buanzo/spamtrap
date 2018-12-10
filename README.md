# spamtrap
Simple spamtrap script that integrates imap/pop3 downloading, and smtp sending for reporting to cisco, etc.


## Introduction

A spamtrap is an email address that has NO reasons to receive ANY email
whatsoever. Thus, any email it receives, is most definitely UNWANTED.

That is the definition of spamtrap: https://en.wikipedia.org/wiki/Spamtrap

This python3 application can help you implement your own spamtrap system at
your organization.

## Features

* IMAP to download unwanted email from spamtrap-account
* SMTP to forward unwanted emails to a third party service (RFC822 attach)
* Cisco IronPort integration (updates a dictionary on any number of SSH-authenticated IronPort servers, for blacklisting purposes)
* SpamAssassin integration (not really used, but the python3 module is quite useful so I just upload it here!)

## How to use

1. Configure
2. Execute via cron or else
3. ????
4. Profit!

## IMPORTANT

Spamtraps have vulnerabilities. If you rely on this tool for fully automated spamtrapping, YOU WILL SUFFER. Your organization will suffer, etc, etc, etc. This *needs* human intervention.

## TODO - If you want to help:

* CRITICAL: implement RFC 2047 decoding and better sender address determination
* Implement POP3 (well, yes, this is an inhouse solution and we use imap!)
* Fix and implement all that is documented in-code
* implement config file
* self-domain detection [good when an account gets taken]


