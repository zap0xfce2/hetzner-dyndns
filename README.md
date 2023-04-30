# Hetzner Dyndns

Ein kleines Python Script welches dafür genutzt werden kann den DNS Record von Hetzner auf die eigene IP zu setzten.

## Verwendung

Es wird eine .env Datei mit folgenden einträgen benötigt:

```bash
DNS_ZONE='meinedomaine.de'
DYNDNS_NAMES='subdomaine'
API_KEY='meinAPIKey'
```

Ein API Key kann in der Hetzner DNS Console erstellt werden (Manage API tokens)

## Dank

Mein Dank geht an Philip welcher auf https://thedatabaseme.de/2022/01/04/hetzner-dns-als-dyndns-provider-nutzen-mit-ansible/ erklärt hat wie das ganze mit Ansible läuft.
