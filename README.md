# Hetzner Dyndns

Ein kleines Python Script welches dafür genutzt werden kann den DNS Record von Hetzner auf die eigene IP zu setzten.

## Verwendung

Es wird eine .env Datei mit folgenden Einträgen benötigt:

```bash
DNS_ZONE='meinedomain.de'
DYNDNS_NAMES='subdomain1,subdomain2'
API_KEY='meinAPIKey'
```

Ein API Key kann in der Hetzner DNS Console erstellt werden (Manage API tokens). Als DYNDNS_NAMES kann entweder ein Wert oder von Komma getrennte Werte angegeben werden.

## Dank

Mein Dank geht an Philip welcher auf https://thedatabaseme.de/2022/01/04/hetzner-dns-als-dyndns-provider-nutzen-mit-ansible/ erklärt hat wie das ganze mit Ansible läuft.
