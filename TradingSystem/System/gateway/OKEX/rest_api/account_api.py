from .client import Client
from .consts import *

class AccountAPI(Client):

    def __init__(self, api_key, api_secret_key, passphrase, proxies, test=True):
        Client.__init__(self, api_key, api_secret_key, passphrase, proxies, test)

    def get_position_risk(self, instType = ""):
        params = {}
        if instType:
            params["instType"] = instType
        return self._request_with_params(GET, ACCOUNT_POSITION_RISK, params)

    def get_balance(self, ccy=""):
        params = {}
        if ccy:
            params["ccy"] = ccy
        return self._request_with_params(GET, ACCOUNT_BALANCE, params)

    def get_positions(self, instType="", instId="", postId=""):
        params = {}
        if instType:
            params["instType"] = instType
        if instId:
            params["instId"] = instId
        if postId:
            params["postId"] = postId
        return self._request_with_params(GET, ACCOUNT_POSITIONS, params)

    def get_bills_week(self, instType="", ccy="", mgnMode="", ctType="", type="", subType="", after="", before="", limit=100):
        params = {}
        if instType:
            params["instType"] = instType
        if mgnMode:
            params["mgnMode"] = mgnMode
        if ctType:
            params["ctType"] = ctType
        if type:
            params["type"] = type
        if subType:
            params["subType"] = subType
        if after:
            params["after"] = after
        if before:
            params["before"] = before
        if limit:
            params["limit"] = limit
        return self._request_with_params(GET, ACCOUNT_BILLS_WEEK, params)

    def get_config(self):
        return self._request_without_params(GET, ACCOUNT_CONFIG)