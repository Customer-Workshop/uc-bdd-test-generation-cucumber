# InvestRight Trading API

A Spring Boot application that integrates with the [InvestRight Open API](https://developer.hdfcsec.com/ir-docs/docs/intro) for automated trading, with OCR-based trade signal parsing from images.

## Features

- **Authentication**: Full InvestRight login flow (credentials, 2FA, access token)
- **Order Management**: Place, modify, cancel orders and check status
- **Image OCR Parsing**: Upload trade signal images → AWS Textract OCR → automatic order placement
- **Symbol Mapping**: Maps short names to InvestRight-compatible trading symbols
- **Swagger UI**: Interactive API documentation at `/swagger-ui.html`

## Prerequisites

- **Java 17+**
- **Maven 3.8+**
- **AWS account** with Textract access (for OCR image parsing)
- **InvestRight API credentials** (API key, API secret)

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd investright-trading-api
```

### 2. Configure environment variables

```bash
export IR_API_KEY=your_investright_api_key
export IR_API_SECRET=your_investright_api_secret
```

Or create an `.env` file (not committed to git):
```
IR_API_KEY=your_api_key
IR_API_SECRET=your_api_secret
```

### 3. Build and run

```bash
mvn clean install
mvn spring-boot:run
```

The API will start on `http://localhost:8080`.

### 4. Access Swagger UI

Open http://localhost:8080/swagger-ui.html in your browser.

## API Usage Examples

### Authentication

#### Step 1: Get Token ID
```bash
curl -X POST http://localhost:8080/api/auth/token
```

#### Step 2: Login with credentials
```bash
curl -X POST 'http://localhost:8080/api/auth/login?tokenId=YOUR_TOKEN_ID' \
  -H 'Content-Type: application/json' \
  -d '{"username": "your_username", "password": "your_password"}'
```

#### Step 3: Validate 2FA
```bash
curl -X POST 'http://localhost:8080/api/auth/validate-2fa?tokenId=YOUR_TOKEN_ID' \
  -H 'Content-Type: application/json' \
  -d '{"answer": "123456"}'
```

#### Step 4: Authorize
```bash
curl -X POST 'http://localhost:8080/api/auth/authorize?tokenId=YOUR_TOKEN_ID&requestToken=YOUR_REQUEST_TOKEN&consent=true'
```

#### Step 5: Get Access Token
```bash
curl -X POST 'http://localhost:8080/api/auth/access-token?requestToken=YOUR_REQUEST_TOKEN'
```

#### Full Login (all steps in one call)
```bash
curl -X POST 'http://localhost:8080/api/auth/full-login?twoFaAnswer=123456' \
  -H 'Content-Type: application/json' \
  -d '{"username": "your_username", "password": "your_password"}'
```

### Place Order

```bash
curl -X POST 'http://localhost:8080/api/orders/place?userId=your_username' \
  -H 'Content-Type: application/json' \
  -u user:password \
  -d '{
    "exchange": "NSE",
    "securityId": "RELIANCE",
    "instrumentSegment": "EQUITY",
    "transactionType": "BUY",
    "product": "DELIVERY",
    "orderType": "LIMIT",
    "price": 2500,
    "triggerPrice": 0,
    "quantity": 1,
    "validity": "DAY"
  }'
```

### Place Option Order

```bash
curl -X POST 'http://localhost:8080/api/orders/place?userId=your_username' \
  -H 'Content-Type: application/json' \
  -u user:password \
  -d '{
    "exchange": "NSE",
    "securityId": "68180",
    "underlyingSymbol": "NIFTYEQEQNR",
    "instrumentSegment": "OPTIDX",
    "transactionType": "BUY",
    "product": "OVERNIGHT",
    "orderType": "MARKET",
    "price": 0,
    "triggerPrice": 0,
    "quantity": 50,
    "optionType": "CE",
    "strikePrice": 22400,
    "expiryDate": "20240425",
    "validity": "DAY"
  }'
```

### Cancel Order

```bash
curl -X DELETE 'http://localhost:8080/api/orders/12345?userId=your_username' \
  -u user:password
```

### Get Order Status

```bash
curl 'http://localhost:8080/api/orders/status/12345?userId=your_username' \
  -u user:password
```

### Parse Trade Signals from Image

```bash
curl -X POST http://localhost:8080/api/signals/parse-image \
  -u user:password \
  -F 'image=@/path/to/trade-signal-image.png'
```

### Execute Trades from Image

```bash
curl -X POST 'http://localhost:8080/api/signals/execute-image?userId=your_username&quantityOverride=10' \
  -u user:password \
  -F 'image=@/path/to/trade-signal-image.png'
```

## Image Format Requirements for OCR

For best OCR accuracy:
- Use **PNG or TIFF** format (avoid JPEG compression artifacts)
- Minimum resolution: **300 DPI**
- Clear, well-lit images with **high contrast** text
- Table structure with clear row/column separators
- Text should contain trade signals in the format:
  ```
  MAZDOCK 2760CE BUY ABOVE 150 SL 120 TGT 180 200 220
  RECLTD 370PE SELL BELOW 45 SL 55 TARGET 35 25
  RELIANCE BUY ABOVE 2500 SL 2450 TGT 2550 2600
  ```

## Scheduled Trade Agent

The application includes a built-in scheduled agent that automatically:
1. Logs into InvestRight at a configured time daily (8:55 AM IST by default)
2. Reads trade signal images from your local `C:\trades` folder (or cloud URLs)
3. Parses them via OCR
4. Places buy/sell orders automatically

### Quick Start (Windows — Local Folder)

**Prerequisites:**
1. Install [Java 17+](https://adoptium.net/)
2. AWS credentials configured (for Textract OCR) — use `aws configure` or set `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`

**Step 1: Set environment variables** (run in PowerShell or add to System Environment Variables):

```powershell
$env:SCHEDULER_ENABLED = "true"
$env:TRADE_FOLDER_PATH = "C:\trades"
$env:IR_API_KEY = "your_api_key"
$env:IR_API_SECRET = "your_api_secret"
$env:IR_USERNAME = "your_investright_username"
$env:IR_PASSWORD = "your_investright_password"
$env:IR_2FA_ANSWER = "your_2fa_code"
$env:IR_USER_ID = "your_client_id"
```

**Step 2: Build and run the application:**

```powershell
cd investright-trading-api
mvn clean package -DskipTests
java -jar target/investright-trading-api-1.0.0.jar
```

**Step 3: Place your trade signal images** in `C:\trades` before 8:55 AM IST. The agent will automatically:
- Read all PNG/JPG/TIFF/BMP images from the folder
- OCR parse each image for trade signals
- Place buy/sell orders on InvestRight

### Auto-Start on Windows Boot

To have the app start automatically when Windows boots, create a Windows Task Scheduler task:
1. Open Task Scheduler → Create Basic Task
2. Trigger: "When the computer starts"
3. Action: Start a program → `javaw.exe`
4. Arguments: `-jar C:\path\to\investright-trading-api-1.0.0.jar`
5. Set "Run whether user is logged on or not"

### Configuration

Customize the schedule and image source in `application.yml`:

```yaml
scheduler:
  enabled: true
  cron: "0 55 8 * * *"        # 8:55 AM daily
  timezone: Asia/Kolkata
  image-source: local          # "local" for folder, "cloud" for URLs
  local-folder-path: C:\trades
  use-date-subfolder: false    # if true, reads from C:\trades\2024-04-25\ (today's date)
  auto-login: true
  retry-attempts: 3
```

#### Date Subfolder Mode

If you organize images by date, enable `use-date-subfolder: true`. The agent will look for a subfolder named with today's date (format: `yyyy-MM-dd`):
```
C:\trades\
├── 2024-04-25\      ← today's images (auto-selected)
│   ├── signal1.png
│   └── signal2.png
├── 2024-04-24\      ← yesterday (ignored)
```

### S3 Source (AWS)

Upload trade signal CSV/image files to an S3 bucket, and the app reads them automatically:

```yaml
scheduler:
  image-source: s3
  use-date-subfolder: true   # reads from s3://bucket/trade-signals/2024-04-25/

aws:
  region: ap-south-1
  s3:
    bucket-name: my-trade-signals
    prefix: trade-signals/
```

**S3 bucket structure:**
```
my-trade-signals/
├── trade-signals/
│   ├── 2024-04-25/          ← today (auto-selected when use-date-subfolder=true)
│   │   ├── signals.csv
│   │   └── chart.png
│   └── 2024-04-24/          ← yesterday (ignored)
```

**IAM permissions needed:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::my-trade-signals",
        "arn:aws:s3:::my-trade-signals/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["textract:DetectDocumentText"],
      "Resource": "*"
    }
  ]
}
```

**Authentication options:**
- **IAM Role (recommended on EC2):** Attach a role to the EC2 instance — no keys needed
- **Environment variables:** `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- **AWS credentials file:** `~/.aws/credentials`

### Cloud Source (Alternative)

If you prefer cloud storage instead of a local folder, set `image-source: cloud`:

```yaml
scheduler:
  image-source: cloud
  image-source-url: https://s3.example.com/trades.png
  image-source-urls:
    - https://drive.google.com/uc?export=download&id=FILE_ID
```

| Provider | URL Format |
|---|---|
| **AWS S3** | Pre-signed URL: `https://bucket.s3.region.amazonaws.com/key?X-Amz-...` |
| **Google Drive** | Direct download: `https://drive.google.com/uc?export=download&id=FILE_ID` |
| **Azure Blob** | SAS URL: `https://account.blob.core.windows.net/container/blob?sv=...` |
| **Direct URL** | Any publicly accessible image URL |

### Telegram Channel Source

Read trade signals directly from a Telegram channel. This runs **alongside** your existing image/CSV/S3 source — signals from both sources are combined.

**Step 1: Create a Telegram Bot**
1. Open Telegram, search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the **bot token** (e.g., `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

**Step 2: Add the bot to your channel**
1. Open your Telegram channel settings
2. Go to **Administrators** → **Add Administrator**
3. Search for your bot name and add it
4. The bot only needs **read** permission

**Step 3: Get the channel ID**
1. Forward a message from the channel to [@userinfobot](https://t.me/userinfobot)
2. The bot will reply with the channel ID (e.g., `-1001234567890`)

**Step 4: Configure environment variables**
```bash
export TELEGRAM_ENABLED=true
export TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
export TELEGRAM_CHANNEL_ID=-1001234567890
export TELEGRAM_CAPITAL_PER_TRADE=40000    # ₹40,000 per Telegram trade
export TELEGRAM_LOOKBACK_MINUTES=30         # Read messages from last 30 minutes
```

Or in `application.yml`:
```yaml
telegram:
  enabled: true
  bot-token: ${TELEGRAM_BOT_TOKEN}
  channel-id: ${TELEGRAM_CHANNEL_ID}
  capital-per-trade: 40000
  lookback-minutes: 30
```

**Supported message format:**
```
HERO ZERO
BUY SENSEX 76600PE ABV 200 TGT
240-280-350
SL 165
INTRADAY
```

**Multi-source mode:** When Telegram is enabled, it reads from **both** your primary source (local/S3/cloud) AND Telegram. Image/CSV trades use ₹1,00,000 capital (default), Telegram trades use ₹40,000.

## AWS Deployment

### Option 1: Docker (Recommended)

```bash
# Build the Docker image
docker build -t investright-trading-api .

# Run with environment variables
docker run -d --name investright \
  -p 8080:8080 \
  -e IR_API_KEY=your_key \
  -e IR_API_SECRET=your_secret \
  -e IR_USERNAME=your_username \
  -e IR_PASSWORD=your_password \
  -e IR_2FA_ANSWER=your_mpin \
  -e SCHEDULER_ENABLED=true \
  -e TRADE_IMAGE_SOURCE=s3 \
  -e S3_BUCKET_NAME=my-trade-signals \
  -e AWS_REGION=ap-south-1 \
  -v trade-data:/app/trades \
  investright-trading-api
```

Or use docker-compose:
```bash
cd deploy
cp .env.example .env  # edit with your credentials
docker-compose up -d
```

### Option 2: EC2 Direct

```bash
# 1. SSH into your EC2 instance (Mumbai region recommended)
ssh ec2-user@your-ec2-ip

# 2. Run the setup script
chmod +x ec2-startup.sh
sudo ./ec2-startup.sh

# 3. Copy your JAR file
scp target/investright-trading-api-0.0.1-SNAPSHOT.jar ec2-user@your-ec2-ip:/opt/investright-trading-api/app.jar

# 4. Edit credentials
sudo nano /opt/investright-trading-api/.env

# 5. Start the service
sudo systemctl start investright-trading-api
```

### Cost Optimization

The app only runs during market hours (8:55 AM — 3:30 PM IST). Use AWS EventBridge to auto-start/stop your EC2 instance:
- **Start rule:** Cron `45 3 ? * MON-FRI *` (UTC = 8:45 AM IST)
- **Stop rule:** Cron `10 10 ? * MON-FRI *` (UTC = 3:40 PM IST)

This reduces EC2 costs by ~70%.

### AWS Secrets Manager (Recommended for Credentials)

Instead of storing credentials in environment variables or config files, use AWS Secrets Manager:

1. Store your credentials as a JSON secret named `investright/trading-api/credentials`
2. Enable Secrets Manager in the app:
```bash
export AWS_SECRETS_MANAGER_ENABLED=true
export AWS_SECRET_NAME=investright/trading-api/credentials
export AWS_REGION=ap-south-1
```

The app loads credentials at startup from Secrets Manager and falls back to env vars if Secrets Manager is unavailable.

**Required IAM permission:**
```json
{
  "Effect": "Allow",
  "Action": "secretsmanager:GetSecretValue",
  "Resource": "arn:aws:secretsmanager:ap-south-1:ACCOUNT_ID:secret:investright/trading-api/credentials-*"
}
```

## Configuration Reference

| Property | Description | Default |
|---|---|---|
| `investright.base-url` | InvestRight API base URL | `https://developer.hdfcsec.com/oapi/v1` |
| `investright.api-key` | API key (env: `IR_API_KEY`) | — |
| `investright.api-secret` | API secret (env: `IR_API_SECRET`) | — |
| `trading.default-lot-size` | Default order quantity | `1` |
| `trading.default-product` | Default order product type | `INTRADAY` |
| `trading.default-validity` | Default order validity | `DAY` |
| `trading.slippage-percent` | Price slippage buffer (%) | `0.5` |
| `scheduler.enabled` | Enable scheduled trade agent | `false` |
| `scheduler.cron` | Cron expression for schedule | `0 55 8 * * *` |
| `scheduler.timezone` | Timezone for cron | `Asia/Kolkata` |
| `scheduler.image-source` | Image source type (env: `TRADE_IMAGE_SOURCE`) | `local` |
| `scheduler.local-folder-path` | Local folder path (env: `TRADE_FOLDER_PATH`) | `C:\trades` |
| `scheduler.use-date-subfolder` | Use today's date as subfolder | `false` |
| `scheduler.image-source-url` | Cloud image URL (env: `TRADE_IMAGE_URL`) | — |
| `scheduler.username` | Auto-login username (env: `IR_USERNAME`) | — |
| `scheduler.password` | Auto-login password (env: `IR_PASSWORD`) | — |
| `scheduler.two-fa-answer` | 2FA code (env: `IR_2FA_ANSWER`) | — |
| `telegram.enabled` | Enable Telegram source (env: `TELEGRAM_ENABLED`) | `false` |
| `telegram.bot-token` | Telegram Bot API token (env: `TELEGRAM_BOT_TOKEN`) | — |
| `telegram.channel-id` | Telegram channel ID (env: `TELEGRAM_CHANNEL_ID`) | — |
| `telegram.capital-per-trade` | Capital per Telegram trade (env: `TELEGRAM_CAPITAL_PER_TRADE`) | `40000` |
| `telegram.lookback-minutes` | Read messages from last N minutes (env: `TELEGRAM_LOOKBACK_MINUTES`) | `30` |
| `aws.region` | AWS region (env: `AWS_REGION`) | `ap-south-1` |
| `aws.s3.bucket-name` | S3 bucket name (env: `S3_BUCKET_NAME`) | — |
| `aws.s3.prefix` | S3 key prefix (env: `S3_PREFIX`) | `trade-signals/` |
| `aws.secrets-manager.enabled` | Enable Secrets Manager (env: `AWS_SECRETS_MANAGER_ENABLED`) | `false` |
| `aws.secrets-manager.secret-name` | Secret name (env: `AWS_SECRET_NAME`) | `investright/trading-api/credentials` |

## Project Structure

```
com.trading.investright
├── config/          # WebClient, Textract, Security, Scheduler, AWS/S3, Properties configs
├── controller/      # AuthController, OrderController, TradeSignalController
├── service/         # OrderService, SymbolMappingService, CloudImageFetcher, LocalImageFetcher, S3TradeSignalFetcher
├── client/          # InvestRightAuthClient, InvestRightOrderClient, ApiRetryHandler
├── model/           # DTOs (request/response), TradeSignal, TradePosition, AuthSession
├── ocr/             # ImageParserService, TradeSignalParser, CsvTradeSignalParser
├── scheduler/       # ScheduledTradeExecutor, PriceMonitorService, PreMarketMonitorService, DailyReportService
└── exception/       # GlobalExceptionHandler, custom exceptions

deploy/
├── ec2-startup.sh       # EC2 setup script (installs Java, creates systemd service)
├── docker-compose.yml   # Docker Compose for one-command deployment
Dockerfile               # Multi-stage Docker build
```

## Running Tests

```bash
mvn test
```

## License

This project is for internal use only.
