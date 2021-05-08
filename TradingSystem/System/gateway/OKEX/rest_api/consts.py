
API_URL = 'https://www.okex.com'

CONTENT_TYPE = 'Content-Type'
OK_ACCESS_KEY = "OK-ACCESS-KEY"
OK_ACCESS_SIGN = "OK-ACCESS-SIGN"
OK_ACCESS_TIMESTAMP = "OK-ACCESS-TIMESTAMP"
OK_ACCESS_PASSPHRASE = "OK-ACCESS-PASSPHRASE"

ACEEPT = 'Accept'
COOKIE = 'Cookie'
LOCALE = 'Locale='

APPLICATION_JSON = 'application/json'

GET = "GET"
POST = "POST"
DELETE = "DELETE"

SERVER_TIMESTAMP_URL = "/api/v5/public/time"

# get的行为不具体写明，其他行为标明

# account
ACCOUNT_POSITION_RISK = "/api/v5/account/account-position-risk"
ACCOUNT_BALANCE = "/api/v5/account/balance"
ACCOUNT_POSITIONS = "/api/v5/account/positions"
ACCOUNT_BILLS_WEEK = "/api/v5/account/bills"
ACCOUNT_BILLS_MONTH = "/api/v5/account/bills-archive"
ACCOUNT_CONFIG = "/api/v5/account/config"
ACCOUNT_SET_POSITION_MODE = "/api/v5/account/set-position-mode"
ACCOUNT_SET_LEVERAGE = "/api/v5/account/set-leverage"
ACCOUNT_MAX_SIZE = "/api/v5/account/max-size"
ACCOUNT_MAX_AVAil_SIZE = "/api/v5/account/max-avail-size"
ACCOUNT_MODIFY_MARGIN_BALANCE = "/api/v5/account/margin-balance"
ACCOUNT_LEVERAGE_INFO = "/api/v5/account/leverage-info"
ACCOUNT_MAX_LOAN = "/api/v5/account/max-loan"
ACCOUNT_TRADE_FEE = "/api/v5/account/trade-fee"
ACCOUNT_INTEREST_RECORD = "/api/v5/account/interest-accrued"
ACCOUNT_SET_GREEKS = "/api/v5/account/set-greeks"
ACCOUNT_MAX_WITHDRAWAL = "/api/v5/account/max-withdrawal"

# assest
ASSEST_DEPOSIT_ADDRESS = "/api/v5/asset/deposit-address"
ASSEST_BALANCE = "/api/v5/asset/balances"
ASSEST_TRANSFER = "/api/v5/asset/transfer"
ASSEST_WITHDRAWAL = "/api/v5/asset/withdrawal"
ASSEST_DEPOSIT_hist = "/api/v5/asset/deposit-history"
ASSEST_WITHDRAWAL_RECORD = "/api/v5/asset/withdrawal-history"
ASSEST_CURRENCIES_INFO = "/api/v5/asset/currencies"
ASSEST_PURCHASE_REDEMPT = "/api/v5/asset/purchase_redempt"
ASSEST_BILLS = "/api/v5/asset/bills"

# market
MARKET_TICKERS = "/api/v5/market/tickers"
MARKET_SPECIFIC_TICKER = "/api/v5/market/ticker"
MARKET_INDEX_TICKERS = "/api/v5/market/index-tickers"
MARKET_DEPTH = "/api/v5/market/books"
MARKET_KLINE = "/api/v5/market/candles"
MARKET_HIST_KLINE = "/api/v5/market/history-candles"
MARKET_INDEX_KLINE = "/api/v5/market/index-candles"
MARKET_MARK_PRICE_KLINE = "/api/v5/market/mark-price-candles"
MARKET_TRADES = "/api/v5/market/trades"

# public
PUBLIC_PRODUCT_BASIC_INFO = "/api/v5/public/instruments"
PUBLIC_DELIVERY_EXERCISE_RECORD = "/api/v5/public/delivery-execrise-history"
PUBLIC_OPEN_INTEREST = "/api/v5/public/open-interest"
PUBLIC_SWAP_FUNDING_RATE = "/api/v5/public/funding-rate"
PUBLIC_SWAP_FUNDING_RATE_HIST = "/api/v5/public/funding-rate-history"
PUBLIC_PRICE_LIMIT = "/api/v5/public/price-limit"
PUBLIC_OPTION_INFO = "/api/v5/public/opt-summary"
PUBLIC_ESTIMATED_PRICE = "/api/v5/public/estimated-price"
PUBLIC_DISCOUNT_RATE_INTEREST_FREE_QUOTA = "/api/v5/public/DISCOUNT-RATE-INTEREST-FREE-QUOTA"
PUBLIC_SYSTEM_TIME = "/api/v5/public/time"
PUBLIC_MARK_PRICE = "/api/v5/public/mark-price"

# trade
TRADE_SET_ORDER = "/api/v5/trade/order"
TRADE_SET_BATCH_ORDERS = "/api/v5/trade/batch-orders"
TRADE_CANCEL_ORDER = "/api/v5/trade/cancel-order"
TRADE_CANCEL_BATCH_ORDERS = "/api/v5/trade/cancel-batch-orders"
TRADE_AMEND_ORDER = "/api/v5/trade/amend-order"
TRADE_AMEND_BATCH_ORDER = "/api/v5/trade/amend-batch-orders"
TRADE_CLOSE_POSITION = "/api/v5/trade/close-postion"
TRADE_ORDER_INFO = "/api/v5/trade/order"
TRADE_PENDING_ORDERS = "/api/v5/trade/orders-pending"
TRADE_ORDERS_HIST_WEEK = "/api/v5/trade/orders-history"
TRADE_ORDERS_HIST_MONTH = "/api/v5/trade/orders-history-archive"
TRADE_FILLS = "/api/v5/trade/fills"
TRADE_SET_ORDER_ALGO = "/api/v5/trade/order-algo"
TRADE_CANCEL_ORDER_ALGO = "/api/v5/trade/cancel-algos"
TRADE_PENDING_ORDERS_ALGO = "/api/v5/trade/orders-algo-pending"
TRADE_ORDERS_ALGO_HIST = "/api/v5/trade/orders-algo-history"

# subaccount
SUBACCOUNT_BALANCES = "/api/v5/account/subaccount/balances"
SUBACCOUNT_BILLS = "/api/v5/account/subaccount/bills"
SUBACCOUNT_MODIFY_APIKEY = "/api/v5/account/subaccount/modify-apikey"
SUBACCOUNT_SET_APIKEY = "/api/v5/account/subaccount/apikey"
SUBACCOUNT_LIST = "/api/v5/account/subaccount/list"
SUBACCOUNT_TRANSFER = "/api/v5/account/subaccount/transfer"