# Hetzner Dyndns

Ein kleines Python Script welches dafür genutzt werden kann den DNS Record von Hetzner auf die eigene IP zu setzten.

## Verwendung

Es wird eine .env Datei mit folgenden Einträgen benötigt:

```bash
DNS_ZONE='meinedomain.de'
DYNDNS_NAMES='subdomain1,subdomain2'
API_KEY='meinAPIKey'
```

Ein API Key kann in der Hetzner Console erstellt werden (Sicherheit->API-Tokens). Als DYNDNS_NAMES kann entweder ein Wert oder von Komma getrennte Werte angegeben werden.
