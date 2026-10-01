# AOOSTAR TrueNAS LCD

TrueNAS SCALE adaptation of `xavtb78/aoostar-proxmox-lcd` for the AOOSTAR WTR MAX LCD.

The image keeps the upstream Flask web editor and `aoostar-rs` LCD tooling, and replaces the Proxmox-specific metrics layer with a TrueNAS-oriented sensor provider.

## What is included

- AOOSTAR LCD access through `/dev/ttyACM0`
- `asterctl` and `aster-sysinfo` built from `zehnm/aoostar-rs`
- upstream visual web editor on TCP port `8765`
- TrueNAS sensor provider
- persistent LCD/editor configuration
- GitHub Actions build and publish to GHCR
- ready-to-paste `truenas-app.yaml`

## Publish the image

The included `setup-project.ps1` is intended for Windows. It creates/updates `D:\Daten\git\aoostar-truenas-lcd`, initializes Git, creates the GitHub repository when GitHub CLI (`gh`) is available, pushes `main`, and waits for the Docker workflow.

After a successful workflow the image is:

`ghcr.io/<github-user>/aoostar-truenas-lcd:latest`

## TrueNAS installation

1. Confirm the LCD exists as `/dev/ttyACM0` on TrueNAS.
2. Open `truenas-app.yaml` and ensure the GHCR image contains your GitHub username.
3. In TrueNAS SCALE open **Apps -> Discover Apps -> menu -> Install via YAML**.
4. App name: `aoostar-truenas-lcd`.
5. Paste the YAML and save.
6. Open `http://<TRUENAS-IP>:8765`.

The default YAML uses a Docker-managed persistent volume for `/app/cfg`, so no pool path needs to be edited. You can replace it later with a TrueNAS host-path dataset if desired.

## TrueNAS API (optional)

The web editor and hardware/LCD functions can start without an API key. Deeper TrueNAS data requires API credentials. Configure these environment variables in the YAML when ready:

- `TRUENAS_API_USER`
- `TRUENAS_API_KEY`
- `TRUENAS_VERIFY_TLS`
- `TRUENAS_NET_IFACE`

Do not commit a real API key to GitHub. Put it only into the YAML pasted into your TrueNAS instance.

## First diagnostics

On TrueNAS shell:

```bash
ls -l /dev/ttyACM*
lsusb | grep -i -E '0416|Winbond'
```

Then inspect the app logs in the TrueNAS UI. The editor remains available even if the LCD device is missing, which helps troubleshooting.

## Credits

This adaptation builds on:

- https://github.com/xavtb78/aoostar-proxmox-lcd
- https://github.com/zehnm/aoostar-rs

Review and preserve the applicable upstream licenses when publishing or redistributing this derivative project.
