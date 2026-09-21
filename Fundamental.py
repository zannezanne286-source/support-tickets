# fundamental.py

import requests
import time


class FundamentalAnalyzer:
    def __init__(self):
        self.results = {}
        self._cache = {}
        self._cache_ttl = 300

    def fetch_fear_greed(self):
        cache_key = "fear_greed"
        if self._is_cached(cache_key):
            return self._cache[cache_key]
        try:
            url = "https://api.alternative.me/fng/?limit=1"
            r = requests.get(url, timeout=10)
            data = r.json()
            value = int(data["data"][0]["value"])
            classification = data["data"][0]["value_classification"]
            if value <= 20:
                signal = f"PEUR EXTREME ({value})"
                score = +2
            elif value <= 40:
                signal = f"PEUR ({value})"
                score = +1
            elif value <= 60:
                signal = f"NEUTRE ({value})"
                score = 0
            elif value <= 80:
                signal = f"CUPIDITE ({value})"
                score = -1
            else:
                signal = f"CUPIDITE EXTREME ({value})"
                score = -2
            self._cache[cache_key] = {"value": value, "classification": classification, "signal": signal, "score": score}
            self._cache[f"{cache_key}_ts"] = time.time()
            return self._cache[cache_key]
        except Exception as e:
            print(f"Erreur Fear & Greed : {e}")
            return {"value": None, "signal": "DONNEES INDISPONIBLES", "score": 0}

    def fetch_global_market(self):
        cache_key = "global_market"
        if self._is_cached(cache_key):
            return self._cache[cache_key]
        try:
            url = "https://api.coingecko.com/api/v3/global"
            r = requests.get(url, timeout=10)
            data = r.json()["data"]
            total_mcap = data["total_market_cap"]["usd"]
            btc_dominance = data["market_cap_percentage"]["btc"]
            eth_dominance = data["market_cap_percentage"]["eth"]
            mcap_change_24h = data["market_cap_change_percentage_24h_usd"]
            if mcap_change_24h > 3:
                signal = f"MARCHE EN HAUSSE (+{mcap_change_24h:.1f}% 24h)"
                score = +1
            elif mcap_change_24h < -3:
                signal = f"MARCHE EN BAISSE ({mcap_change_24h:.1f}% 24h)"
                score = -1
            else:
                signal = f"MARCHE STABLE ({mcap_change_24h:+.1f}% 24h)"
                score = 0
            self._cache[cache_key] = {
                "total_mcap": total_mcap, "btc_dominance": btc_dominance,
                "eth_dominance": eth_dominance, "change_24h": mcap_change_24h,
                "signal": signal, "score": score
            }
            self._cache[f"{cache_key}_ts"] = time.time()
            return self._cache[cache_key]
        except Exception as e:
            print(f"Erreur Market Global : {e}")
            return {"signal": "DONNEES INDISPONIBLES", "score": 0}

    def fetch_news(self, symbol="BTC", limit=10):
        cache_key = f"news_{symbol}"
        if self._is_cached(cache_key):
            return self._cache[cache_key]
        try:
            url = f"https://cryptopanic.com/api/v1/posts/?auth_token=public&currencies={symbol}&public=true"
            r = requests.get(url, timeout=10)
            data = r.json()
            posts = data.get("results", [])[:limit]
            news_list = []
            bullish_count = 0
            bearish_count = 0
            for post in posts:
                title = post.get("title", "")
                votes = post.get("votes", {})
                positive = votes.get("positive", 0)
                negative = votes.get("negative", 0)
                if positive > negative:
                    sentiment = "HAUSSIER"
                    bullish_count += 1
                elif negative > positive:
                    sentiment = "BAISSIER"
                    bearish_count += 1
                else:
                    sentiment = "NEUTRE"
                news_list.append({"title": title, "sentiment": sentiment, "positive": positive, "negative": negative})
            if bullish_count > bearish_count * 1.5:
                signal = f"NEWS HAUSSIERES ({bullish_count}/{bearish_count})"
                score = +1
            elif bearish_count > bullish_count * 1.5:
                signal = f"NEWS BAISSIERES ({bullish_count}/{bearish_count})"
                score = -1
            else:
                signal = f"NEWS NEUTRES ({bullish_count}/{bearish_count})"
                score = 0
            self._cache[cache_key] = {"news": news_list, "bullish": bullish_count, "bearish": bearish_count, "signal": signal, "score": score}
            self._cache[f"{cache_key}_ts"] = time.time()
            return self._cache[cache_key]
        except Exception as e:
            print(f"Erreur News : {e}")
            return {"news": [], "signal": "DONNEES INDISPONIBLES", "score": 0}

    def fetch_coin_data(self, coin_id="bitcoin"):
        cache_key = f"coin_{coin_id}"
        if self._is_cached(cache_key):
            return self._cache[cache_key]
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            params = {"localization": "false", "tickers": "false", "community_data": "false", "developer_data": "false"}
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            market = data.get("market_data", {})
            result = {
                "name": data.get("name"),
                "symbol": data.get("symbol", "").upper(),
                "market_cap": market.get("market_cap", {}).get("usd"),
                "market_cap_rank": data.get("market_cap_rank"),
                "volume_24h": market.get("total_volume", {}).get("usd"),
                "change_24h": market.get("price_change_percentage_24h"),
                "change_7d": market.get("price_change_percentage_7d"),
                "change_30d": market.get("price_change_percentage_30d"),
            }
            self._cache[cache_key] = result
            self._cache[f"{cache_key}_ts"] = time.time()
            return result
        except Exception as e:
            print(f"Erreur CoinGecko {coin_id} : {e}")
            return {"signal": "DONNEES INDISPONIBLES", "score": 0}

    def analyze(self, symbol_base="BTC"):
        coin_map = {
            "BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin",
            "SOL": "solana", "XRP": "ripple", "ADA": "cardano",
            "DOGE": "dogecoin", "AVAX": "avalanche-2", "DOT": "polkadot",
            "MATIC": "matic-network", "LINK": "chainlink", "TON": "the-open-network",
            "SHIB": "shiba-inu", "LTC": "litecoin", "BCH": "bitcoin-cash",
        }
        coin_id = coin_map.get(symbol_base, "bitcoin")
        fg = self.fetch_fear_greed()
        gm = self.fetch_global_market()
        news = self.fetch_news(symbol_base)
        coin = self.fetch_coin_data(coin_id)
        total_score = fg.get("score", 0) + gm.get("score", 0) + news.get("score", 0)
        return {"fear_greed": fg, "global_market": gm, "news": news, "coin_data": coin, "total_score": total_score}

    def _is_cached(self, key):
        if key not in self._cache:
            return False
        return (time.time() - self._cache.get(f"{key}_ts", 0)) < self._cache_ttl
