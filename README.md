# File Share

Temporary file sharing service. Upload via browser, download via `curl`/`wget`. Files expire in 24 hours.

## Deploy on DigitalOcean Droplet

### 1. Create a Droplet

- Image: **Ubuntu 24.04**
- Size: Basic, 1 GB RAM / 1 vCPU ($6/mo) is enough for light usage
- Enable the **Monitoring** checkbox
- Add your SSH key

### 2. SSH into the Droplet

```bash
ssh root@YOUR_DROPLET_IP
```

### 3. Install Docker

```bash
curl -fsSL https://get.docker.com | sh
```

### 4. Clone and Configure

```bash
git clone https://github.com/YOUR_USER/curl_file_sharing.git /opt/fileshare
cd /opt/fileshare
```

Edit `docker-compose.yml` — set your domain:

```yaml
environment:
  - BASE_URL=https://share.yourdomain.com
```

### 5. Start the Service

```bash
docker compose up --build -d
```

The app runs on port `8000`. Verify:

```bash
curl http://localhost:8000/
```

### 6. Set Up Reverse Proxy (Caddy)

Caddy auto-provisions HTTPS via Let's Encrypt.

```bash
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt install -y caddy
```

Create `/etc/caddy/Caddyfile`:

```
share.yourdomain.com {
    reverse_proxy localhost:8000
}
```

```bash
systemctl restart caddy
```

Point your DNS A record for `share.yourdomain.com` to the droplet IP. Caddy handles TLS automatically.

### 7. Firewall

```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable
```

## Usage

Upload via browser at `https://share.yourdomain.com`

Download on any server:

```bash
curl -OJ https://share.yourdomain.com/d/x7Kp2mNq
wget --content-disposition https://share.yourdomain.com/d/x7Kp2mNq
```

## Configuration

Environment variables in `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `http://localhost:8000` | Public URL for download links |
| `MAX_FILE_SIZE` | `209715200` | Max upload size in bytes (200 MB) |
| `FILE_TTL_HOURS` | `24` | Hours before files are deleted |
| `UPLOAD_DIR` | `/data/uploads` | Storage path inside container |

## Maintenance

View logs:

```bash
docker compose logs -f
```

Check cleanup cron:

```bash
docker compose exec fileshare cat /var/log/cleanup.log
```

Restart:

```bash
docker compose restart
```

Update (auto-rebuild on pull):

On the droplet, set up the git hook once:

```bash
cd /opt/fileshare
git config core.hooksPath hooks
```

Now every `git pull` automatically rebuilds the container:

```bash
cd /opt/fileshare
git pull
# container rebuilds automatically
```
