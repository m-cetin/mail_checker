# Mailchecker - Einfache Überprüfung von Mail-Servern

Ein Skript zur Analyse von E-Mail-Servern für SMTP-Smuggling-Schwachstellen.

# Funktionsweise

Das Skript ermöglicht das Senden von E-Mails an einen SMTP-Server und das Beenden der Nachrichten mit verschiedenen fehlerhaften Endzeichenfolgen. Dies dient zum Testen, ob die Server von SMTP-Smuggling-Schwachstellen betroffen sind.

Standardmäßig sendet das Skript eine Test-E-Mail mit einem fehlerhaften Endzeichenfolge ('\n.\n' – Unix-Zeilenumbrüche anstelle von Windows-Zeilenumbrüchen). Es unterstützt jedoch auch mehrere andere fehlerhafte Endungen. Verwenden Sie die Option --list-tests, um die verfügbaren Tests aufzulisten, und --test [Testname], um einen bestimmten Test auszuwählen.

Zum Testen der Postfix-Abhilfemaßnahme steht jetzt ein Pipelining-Test zur Verfügung.

# Überprüfungen
## Standardtest
```
./mail_checker.py mail-server.de
``` 
## Benutzerdefinierter Port sowie TLS
```
./mail_checker.py mail-server.de -s --port 587
```
## Pipelining-Unterstützung überprüfen (Fähigkeit des SMTP-Servers, mehrere Befehle gleichzeitig zu versenden ohne auf eine Bestätigung zu warten)
```
./mail_checker.py mail-server.de --test pipelining
```

## Benutzerdefinierte Absender- und Empfängeradressen mit Authentifizierung:
```
./mail_checker.py -f hans@handwerker-technik.de -t administration@handwerker-technik.de -u meinbenutzername -p meinkennwort mailserver.de
```

## Liste verfügbarer Tests anzeigen
```
./mail_checker.py --list-tests
```

## Bestimmte Tests, z.B. CRCR (Carriage Return Carriage Return, SMTP-Server auf unerwünschte Zeichen testen), durchführen
```
./mail_checker.py mailserver.de --test crcr
```

# Schwachstellen

SMTP-Smuggling-Schwachstellen können auftreten, wenn E-Mail-Server fehlerhafte Endzeichenfolgen akzeptieren. Dies kann dazu führen, dass schadhafte E-Mails an Empfänger gesendet werden, die sie sonst nicht erhalten würden.

Referenzen: 
* [SMTP Smuggling](
  https://sec-consult.com/blog/detail/smtp-smuggling-spoofing-e-mails-worldwide/)
* [Postfix announcement](
  https://www.mail-archive.com/postfix-announce@postfix.org/msg00090.html),[Postfix
  info](https://www.postfix.org/smtp-smuggling.html), [CVE-2023-51764](https://nvd.nist.gov/vuln/detail/CVE-2023-51764)
* [Exim bug report](https://bugs.exim.org/show_bug.cgi?id=3063), [CVE-2023-51766](https://nvd.nist.gov/vuln/detail/CVE-2023-51766)
* [CVE-2023-51765 (SMTP Smuggling in Sendmail)](https://nvd.nist.gov/vuln/detail/CVE-2023-51765)
