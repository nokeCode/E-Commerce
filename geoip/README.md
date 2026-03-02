# GeoIP databases (MaxMind)

The `.mmdb` files are intentionally not versioned in Git.

## 1) Configure your MaxMind license key

PowerShell:

```powershell
$env:MAXMIND_LICENSE_KEY="YOUR_MAXMIND_LICENSE_KEY"
```

## 2) Download databases

From project root (`HStore/`):

```powershell
python scripts/download_geoip.py
```

By default this downloads:
- `GeoLite2-City.mmdb`
- `GeoLite2-ASN.mmdb`

into `geoip/`.

## 3) Optional: download only one edition

```powershell
python scripts/download_geoip.py --editions GeoLite2-City
```

## If `.mmdb` files were already committed before

Remove them from Git index without deleting local files:

```powershell
git rm --cached geoip/*.mmdb
git commit -m "Stop tracking GeoIP databases"
```
