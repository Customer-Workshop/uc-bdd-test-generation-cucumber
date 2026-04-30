# InvestRight Trading API

A Spring Boot application that integrates with the [InvestRight Open API](https://developer.hdfcsec.com/ir-docs/docs/intro) for automated trading, with OCR-based trade signal parsing from images.

## Features

- **Authentication**: Full InvestRight login flow (credentials, 2FA, access token)
- **Order Management**: Place, modify, cancel orders and check status
- **Image OCR Parsing**: Upload trade signal images → automatic order placement
- **Symbol Mapping**: Maps short names to InvestRight-compatible trading symbols
- **Swagger UI**: Interactive API documentation at `/swagger-ui.html`

## Prerequisites

- **Java 17+**
- **Maven 3.8+**
- **Tesseract OCR 4.x+** installed on the system
- **InvestRight API credentials** (API key, API secret)

### Install Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng
```

**macOS (Homebrew):**
```bash
brew install tesseract
```

**Windows:**
Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH.

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

## Configuration Reference

| Property | Description | Default |
|---|---|---|
| `investright.base-url` | InvestRight API base URL | `https://developer.hdfcsec.com/oapi/v1` |
| `investright.api-key` | API key (env: `IR_API_KEY`) | — |
| `investright.api-secret` | API secret (env: `IR_API_SECRET`) | — |
| `tesseract.data-path` | Tesseract tessdata path | `/usr/share/tesseract-ocr/4.00/tessdata` |
| `tesseract.language` | OCR language | `eng` |
| `trading.default-lot-size` | Default order quantity | `1` |
| `trading.default-product` | Default order product type | `INTRADAY` |
| `trading.default-validity` | Default order validity | `DAY` |
| `trading.slippage-percent` | Price slippage buffer (%) | `0.5` |

## Project Structure

```
com.trading.investright
├── config/          # WebClient, Tesseract, Security, Properties configs
├── controller/      # AuthController, OrderController, TradeSignalController
├── service/         # OrderService, SymbolMappingService
├── client/          # InvestRightAuthClient, InvestRightOrderClient
├── model/           # DTOs (request/response), TradeSignal, AuthSession
├── ocr/             # ImageParserService, TradeSignalParser
└── exception/       # GlobalExceptionHandler, custom exceptions
```

## Running Tests

```bash
mvn test
```

## License

This project is for internal use only.
