#!/usr/bin/env python3
import sys
import smtplib
import argparse
import datetime

from imapclient import IMAPClient
from spamassassin import SpamAssassin
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from util import Util
from storage import Storage
from cisco import IronportSSH

from pprint import pprint

# TODO: Configuration should be on a config file
IMAPHOST = ''
IMAPUSER = ''
IMAPPASS = ''
SMTPHOST = IMAPHOST
SMTPUSER = ''
SMTPPASS = ''

# Addresses to send spam, phishing, ham, etc. TODO: enhance, cause all is spam today
CISCO_ADDR = {'spam': 'spam@example.net',
              'phishing': 'phish@example.net',
              'ham': 'ham@example.net'}

# IronPort dictionary name (must exist beforehand, and used in a blacklisting rule)
IRONDICT = 'Mosquitero_From'

class SpamTrapMREC():
    def __init__(self,
                 imapHost=None, imapUser=None, imapPass=None,
                 imapFolder='INBOX',
                 smtpHost=None, smtpUser=None, smtpPass=None,
                 emailFrom=None):
        # Useful pre-loaded lists
        self.IMAPTAGS = ['INTERNALDATE', 'ENVELOPE', 'RFC822']
        self.CRITERIA = ['NOT', 'DELETED']
        # Services
        self.storage = Storage()
        self.util = Util()
        # yeah, this could be better.
        self.ironports = {'iron1': IronportSSH(host='someironporthost'),
                          'iron2': IronportSSH(host='anotherironporthost')}
        # TODO: Validate
        self.emailFrom = emailFrom
        self.imapHost = imapHost
        self.imapUser = imapUser
        self.imapPass = imapPass
        self.smtpHost = smtpHost
        self.smtpUser = smtpUser
        self.smtpPass = smtpPass
        self.imapFolder = imapFolder
        # Setup IMAP
        print("[INFO] Setting up IMAP")
        self.client = IMAPClient(host=self.imapHost)
        self.client.login(self.imapUser, imapPass)
        # pprint(self.client.list_folders())
        # self.client.select_folder('Junk')
        self.client.select_folder(self.imapFolder)
        print("[INFO] IMAP Ready for {} Folder".format(self.imapFolder))
        self.storage.updateExecutionTime()

    def finish(self):
        self.client.logout()
        print()

    def displayMessageDetails(self, message=None, id=None):
        if message is None:
            m = self.msg
            id = self.msgid
        else:
            m = message[id]
        e = m[b'ENVELOPE']
        print("[INFO] Message ID # {} Details:".format(id[0]))
        for fromItem in e.from_:
            print("[INFO] FROM   : {}".format(fromItem))  # TODO: needs more work
        if hasattr(e.subject, 'decode'):
            print("[INFO] SUBJECT: {}".format(e.subject.decode('utf-8')))

    def listMessages(self, folder=None):
        if folder is not None:
            self.client.select_folder(folder)

        ids = self.client.search(self.CRITERIA)
        msgs = self.client.fetch(ids, self.IMAPTAGS)
        print("[INFO] {} messages - Criteria: {}".format(len(msgs),
                                                         self.CRITERIA))
        for id in ids:
            self.msg = msgs[id]
            self.msgid = [id]
            self.displayMessageDetails()

    def getOneMessage(self, spam=False):
        if spam is True:
            print("[INFO] Selecting SPAM Folder")
            self.client.select_folder('Spam')
        try:
            self.msgid = [self.client.search(self.CRITERIA)[0]]
        except:
            self.msgid = None

        if self.msgid is None:
            print("[INFO] No messages.")
            return(None)

        print("[INFO] Got one message (ID # {})".format(self.msgid[0]))

        try:
            self.msg = self.client.fetch(self.msgid,
                                         self.IMAPTAGS)[self.msgid[0]]
        except:
            print("[ERR ] No such msg ID # {}. Exiting.".format(self.msgid[0]))
            sys.exit(1)

        self.getEnvelope()
        return(self.msg)

    def getEnvelope(self):
        self._from = str(self.msg[b'ENVELOPE'].from_[0])

    def analyzeMessage(self):
        print('[INFO] Analyzing message...')
        rfc822 = self.msg[b'RFC822']
        assassin = SpamAssassin(rfc822)
        if (assassin.is_spam()):
            # TODO: set self.spam, self.phishing, etc
            self.msg_is_spam = True
            print("[INFO] SpamaAssassin claims its SPAM")

    def deleteMessage(self, ask=False):
        delmsg = True
        if ask:
            x = self.util.input_sn('Eliminar el mensaje?', default='s')
            if x is False:
                delmsg = False
        if delmsg:
            self.client.delete_messages(self.msgid)

    def refreshCiscoDictionaries(self):
        for spammer in self.storage.getSendersDict():
            for host in self.ironports.keys():
                print("[INFO:IronPort:{}] Adding {}".format(host, spammer))
                self.ironports[host].add_to_dictionary(dictname=IRONDICT,
                                                       what=spammer,
                                                       verbose=True)

    def actOnMessage(self):
        print('[INFO] Acting on message')
        self.storage.increment_from(self._from)
        spammer = self.util.extract_address(self._from)
        # TODO: may need fixing
        print('[INFO] Spammer is {}'.format(spammer))
        for host in self.ironports.keys():
            self.ironports[host].add_to_dictionary(dictname=IRONDICT,
                                                   what=spammer,
                                                   verbose=True)
        self.sendEmail(to=CISCO_ADDR['spam'],
                       subject='SPAMTRAP-received email - RFC822 attached')
        self.storage.updateTrappedTime()

    def sendEmail(self, to=None, subject=None):
        if to is None or subject is None:
            sys.exit(2)
        msg = MIMEMultipart()
        msg['From'] = self.emailFrom
        msg['To'] = to
        msg['Subject'] = subject
        body = """
Hello Team.

This is spamtrap service at blahblah

Please see attached for spamtrap-caught unwanted email.

You might contact a human being at
INFOSEC <blah@example.net>

Thanks.

Sincerely,
SPAMTRAP Service at blah example
"""
        msg.attach(MIMEText(body, 'plain'))
        filename = "unwanted_email_id_{}.txt".format(self.msgid[0])
        attachment = self.msg[b'RFC822']
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        "attachment; filename={}".format(filename))
        msg.attach(part)

        try:
            server = smtplib.SMTP(self.smtpHost, 25)
            server.starttls()
            server.login(self.smtpUser, self.smtpPass)
            text = msg.as_string()
            server.sendmail(self.emailFrom, to, text)
            server.quit()
        except smtplib.SMTPException as e:
            print(str(e))
            print("[ERROR] Cannot send email")
            return
        print("[INFO] Email sent")
        print("[INFO] From={}".format(self.emailFrom))
        print("[INFO] To={}".format(to))
        print("[INFO] Subject={}".format(subject))

if __name__ == '__main__':
    st = SpamTrapMREC(imapHost=IMAPHOST,
                      imapUser=IMAPUSER,
                      imapPass=IMAPPASS,
                      smtpHost=SMTPHOST,
                      smtpUser=SMTPUSER,
                      smtpPass=SMTPPASS,
                      emailFrom=SMTPUSER)
    now = datetime.datetime.now()
    print(now)
    msg = st.getOneMessage()
    if msg is not None:
        st.displayMessageDetails()
        #st.analyzeMessage()
        st.actOnMessage()
        st.deleteMessage()
    st.finish()

    st = SpamTrapMREC(imapHost=IMAPHOST,
                      imapUser=IMAPUSER,
                      imapPass=IMAPPASS,
                      smtpHost=SMTPHOST,
                      smtpUser=SMTPUSER,
                      smtpPass=SMTPPASS,
                      emailFrom=SMTPUSER,
                      imapFolder='Junk')
    # st.refreshCiscoDictionaries()
    msg = st.getOneMessage()
    if msg is not None:
        st.displayMessageDetails()
        st.analyzeMessage()
        st.actOnMessage()
        st.deleteMessage()
    st.finish()
# TODO: implement argparse
# TODO: implement config file
# TODO: implement stat sending over syslog
# TODO: folder selection, --all-folders
# TODO: switches such as --skip-delete
