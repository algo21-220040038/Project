from .client import Client
from .consts import *

class TradeAPI(Client):
    def __init__(self, api_key, api_secret_key, passphrase, proxies, test=True):
        Client.__init__(self, api_key, api_secret_key, passphrase, proxies, test)

    def set_order(self, instId, tdMode, side, ordType, sz, ccy="", clOrdId="", tag="", posSide="", px="", reduceOnly=""):
        params = {}
        params["instId"] = instId
        params["tdMode"] = tdMode
        params["side"] = side
        params["ordType"] = ordType
        params["sz"] = sz
        if ccy:
            params["ccy"] = ccy
        if clOrdId:
            params["clOrdId"] = clOrdId
        if tag:
            params["tag"] = tag
        if posSide:
            params["posSide"] = posSide
        if px:
            params["px"] = px
        if reduceOnly:
            params["reduceOnly"] = reduceOnly
        return self._request_with_params(POST, TRADE_SET_ORDER, params)

    def cancel_order(self, instId, ordId="", clOrdId=""):
        params = {}
        params["instId"] = instId
        if ordId:
            params["ordId"] = ordId
        if clOrdId:
            params["clOrderId"] = clOrdId
        return self._request_with_params(POST, TRADE_CANCEL_ORDER, params)

    def get_order(self, instId, ordId="", clOrderId=""):
        params = {}
        params["instId"] = instId
        if ordId:
            params["ordId"] = ordId
        if clOrderId:
            params["clOrderId"] = clOrderId
        return self._request_with_params(GET, TRADE_ORDER_INFO, params)

    def get_orders_hist_week(self, instType, uly="", instId="", state="", after="", before="", limit="100"):
        params = {}
        params["instType"] = instType
        if uly:
            params["uly"] = uly
        if instId:
            params["instId"] = instId
        if state:
            params["state"] = state
        if after:
            params["after"] = after
        if before:
            params["before"] = before
        if limit:
            params["limit"] = limit
        return self._request_with_params(GET, TRADE_ORDERS_HIST_WEEK, params)

    def get_orders_hist_month(self, instType, uly="", instId="", state="", after="", before="", limit="100"):
        params = {}
        params["instType"] = instType
        if uly:
            params["uly"] = uly
        if instId:
            params["instId"] = instId
        if state:
            params["state"] = state
        if after:
            params["after"] = after
        if before:
            params["before"] = before
        if limit:
            params["limit"] = limit
        return self._request_with_params(GET, TRADE_ORDERS_HIST_MONTH, params)