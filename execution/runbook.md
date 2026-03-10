# Deployment Runbook (Docker + VPS)

## 1. Prepare server
- Install Docker and Docker Compose plugin.
- Open inbound port for webhook or polling traffic.

## 2. Configure environment
- Copy `.env.example` to `.env`.
- Set Telegram token, OpenAI key, PostgreSQL URL, amoCRM credentials.
- Set `DEFAULT_CLIENT_ID` that maps to config file.

## 3. Initialize DB
- Run SQL from `sql/schema.sql`.

## 4. Start services
- Run `docker compose -f docker-compose.yml up -d --build` from `execution/`.

## 5. Verify
- Send test message to bot in RU and EN.
- Confirm lead row appears in DB.
- Trigger risk phrase and verify Telegram card + amoCRM record.

## 6. Operate
- Watch logs for `pending_human` older than SLA (1h).
- Rotate API keys and backup DB regularly.
