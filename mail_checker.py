#!/usr/bin/env python3

import argparse
import base64
import datetime
import email.utils
import socket
import ssl
import sys

def receive_data():
    received_data = sock.recv(4096)
    print(f"\033[1;34mEMPFANGEN:\033[0;36m {received_data.decode()}\033[0m")
    return received_data.decode()

def send_data(message):
    print(f"\033[1;34mSENDEN:\033[0;33m {message}\033[0m")
    sock.send(f"{message}\r\n".encode())

def send_mail_header():
    mail_date = email.utils.format_datetime(datetime.datetime.now())
    msg_id = email.utils.make_msgid(domain=ehlo)

    receive_data()
    send_data(f"EHLO {ehlo}")
    receive_data()

    if args.user and args.password:
        auth_plain = f"\x00{args.user}\x00{args.password}"
        b64 = base64.b64encode(auth_plain.encode()).decode()
        send_data(f"AUTH PLAIN {b64}")
        if not receive_data().startswith("2"):
            sys.exit("Authentifizierung fehlgeschlagen")

    send_data(f"MAIL FROM:<{args.mailfrom}>")
    response = receive_data()
    if not response.startswith("2"):
        sys.exit("Ungültige Absenderadresse")

    send_data(f"RCPT TO:<{args.to}>")
    response = receive_data()
    if not response.startswith("2"):
        sys.exit("Ungültige Empfängeradresse")

    send_data("DATA")
    receive_data()
    send_data(f"From: {args.mailfrom}")
    send_data(f"To: {args.to}")
    send_data("Subject: Hallo Welt")
    send_data(f"Date: {mail_date}")
    send_data(f"Message-ID: {msg_id}")
    send_data("")

def test_bad_end(bad_end_value):
    send_mail_header()
    send_data(f"Dies ist eine Testnachricht mit einem {repr(bad_end_value)} Abschluss.")
    sock.send(bad_end_value.encode())
    try:
        response = receive_data()
    except TimeoutError:
        print(f"Timeout nach 5 Sekunden beim Senden von {repr(bad_end_value)}")
        print("Abschließen der Nachricht mit <CR><LF>.<CR><LF>")
        send_data(f"Dies ist nach einer fehlerhaften Nachricht {repr(bad_end_value)} Abschluss.")
        sock.send("\r\n.\r\n".encode())
        if receive_data().startswith("250 "):
            print(f"Erfolgreich eine Nachricht mit {repr(bad_end_value)} gesendet,")
            print("aber nicht als Nachrichtenende akzeptiert.")
            print("Dies sollte wahrscheinlich abgelehnt werden.")
            print("Die Ergebnisse sollten auf der Empfängerseite analysiert werden.")
        return
    if response.startswith("250 "):
        print(f"Es scheint, als ob {repr(bad_end_value)} akzeptiert wurde (schlecht!)")
    else:
        print(f"Es scheint, als ob der Server {repr(bad_end_value)} nicht akzeptiert hat, das ist wahrscheinlich gut.")

def test_pipelining():
    mail_date = email.utils.format_datetime(datetime.datetime.now())
    msg_id = email.utils.make_msgid(domain=ehlo)

    send_mail_header()
    send_data("Dies ist E-Mail 1/2 zum Testen von Pipelining")
    sock.send("\r\n.\r\n".encode())
    send_data(f"MAIL FROM:<{args.mailfrom}>")
    send_data(f"RCPT TO:<{args.to}>")
    send_data("DATA")
    send_data(f"From: {args.mailfrom}")
    send_data(f"To: {args.to}")
    send_data("Subject: Hallo Welt 2")
    send_data(f"Date: {mail_date}")
    send_data(f"Message-ID: {msg_id}")
    send_data("")
    send_data("Dies ist E-Mail 2/2 zum Testen von Pipelining")
    sock.send("\r\n.\r\n".encode())
    response = receive_data()

    lines = response.splitlines()
    x_line = lines[-2] if len(lines) >= 2 else ""
    if lines[-1].startswith("5") or x_line.startswith("5"):
        print("Server lehnt schlechte Protokollsynchronisation ab (falls Postfix: Abwehr aktiviert)")
    elif lines[-1].startswith("2"):
        print("Server akzeptiert schlechte Protokollsynchronisation.")
        if args.user:
            print("Hinweis: Die Postfix-Abwehr ist nur aktiviert bei unauthentifizierten Verbindungen, Sie haben mit einer authentifizierten Verbindung getestet.")
    else:
        print("Unsicher, wie die Antwort interpretiert werden soll")

ap = argparse.ArgumentParser(description="SMTP-Testskript für verschiedene Testszenarien.")
ap.add_argument("host", nargs="?", help="Der Hostname oder die IP-Adresse des SMTP-Servers.")
ap.add_argument("-f", "--mailfrom", default="alice@example.org", help="Die Absender-E-Mail-Adresse.")
ap.add_argument("-t", "--to", default="bob@example.org", help="Die Empfänger-E-Mail-Adresse.")
ap.add_argument("-e", "--ehlo", help="Der lokale Teil von mailfrom, falls nicht übergeben.")
ap.add_argument("-u", "--user", help="Der Benutzername für die Authentifizierung.")
ap.add_argument("-p", "--password", help="Das Passwort für die Authentifizierung.")
ap.add_argument("-s", "--tls", action="store_true", help="Verwenden von TLS/SMTPS (Port 465).")
ap.add_argument("--port", type=int, help="Benutzerdefinierter Port für die Verbindung.")
ap.add_argument("-c", "--test", default="lflf", help="Der zu testende Fall (Option).")
ap.add_argument("--list-tests", action="store_true", help="Listet verfügbare Tests auf und beendet das Skript.")
args = ap.parse_args()

tests = {
    "lflf": "\n.\n",
    "crcr": "\r.\r",
    "crlf": "\r.\n",
    "lfcr": "\n.\r",
    "nullbefore": "\r\n\x00.\r\n",
    "nullafter": "\r\n\x00.\r\n",
    "pipelining": "Testen, ob der Server Pipelining unterstützt (Postfix-Abwehr).",
}

if args.list_tests:
    for k, v in tests.items():
        if k == "pipelining":
            print(f'"{k}": {v}')
        else:
            print(f'"{k}": Sendet fehlerhaftes {repr(v)} als Ende des DATA-Symbols.')
    sys.exit(0)

if not args.host:
    ap.print_help()
    sys.exit(0)

if args.test not in tests:
    sys.exit("Ungültiger Testfall")

if bool(args.user) != bool(args.password):
    sys.exit("Beide Benutzername und Passwort sind für die Authentifizierung erforderlich.")

print(args)

port = 25
if args.port:
    port = args.port
elif args.tls:
    port = 465

if not args.ehlo:
    ehlo = args.mailfrom.split("@")[-1]
else:
    ehlo = args.ehlo

psock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
psock.settimeout(5)

if args.tls:
    psock.connect((args.host, port))
    context = ssl.create_default_context()
    sock = context.wrap_socket(psock, server_hostname=args.host)
else:
    psock.connect((args.host, port))
    sock = psock

if args.test == "pipelining":
    test_pipelining()
else:
    test_bad_end(tests[args.test])
