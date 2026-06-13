from enum import Enum
from typing import Optional


class Platform(str, Enum):
    AMAZON = "amazon"
    TAOBAO = "taobao"
    TMALL = "tmall"
    JD = "jd"
    PINDUODUO = "pinduoduo"
    DOUYIN = "douyin"
    XIAOHONGSHU = "xiaohongshu"

    @property
    def display_name(self) -> str:
        names = {
            Platform.AMAZON: "Amazon",
            Platform.TAOBAO: "淘宝",
            Platform.TMALL: "天猫",
            Platform.JD: "京东",
            Platform.PINDUODUO: "拼多多",
            Platform.DOUYIN: "抖音电商",
            Platform.XIAOHONGSHU: "小红书",
        }
        return names.get(self, self.value)

    @property
    def base_url(self) -> Optional[str]:
        urls = {
            Platform.AMAZON: "https://www.amazon.com",
            Platform.TAOBAO: "https://www.taobao.com",
            Platform.TMALL: "https://www.tmall.com",
            Platform.JD: "https://www.jd.com",
            Platform.PINDUODUO: "https://www.pinduoduo.com",
            Platform.DOUYIN: "https://www.douyin.com",
            Platform.XIAOHONGSHU: "https://www.xiaohongshu.com",
        }
        return urls.get(self)

    @property
    def bestseller_url(self) -> Optional[str]:
        urls = {
            Platform.AMAZON: "https://www.amazon.com/Best-Sellers/zgbs",
            Platform.TAOBAO: None,
            Platform.TMALL: None,
            Platform.JD: "https://www.jd.com/phb/zhishi/",
            Platform.PINDUODUO: None,
            Platform.DOUYIN: None,
            Platform.XIAOHONGSHU: None,
        }
        return urls.get(self)


class AmazonDomain(str, Enum):
    US = "www.amazon.com"
    JP = "www.amazon.co.jp"
    UK = "www.amazon.co.uk"
    DE = "www.amazon.de"
    FR = "www.amazon.fr"
    IT = "www.amazon.it"
    ES = "www.amazon.es"
    CA = "www.amazon.ca"
    IN = "www.amazon.in"
    AU = "www.amazon.com.au"

    @property
    def country_code(self) -> str:
        codes = {
            AmazonDomain.US: "us",
            AmazonDomain.JP: "jp",
            AmazonDomain.UK: "uk",
            AmazonDomain.DE: "de",
            AmazonDomain.FR: "fr",
            AmazonDomain.IT: "it",
            AmazonDomain.ES: "es",
            AmazonDomain.CA: "ca",
            AmazonDomain.IN: "in",
            AmazonDomain.AU: "au",
        }
        return codes.get(self, "us")

    @property
    def locale_name(self) -> str:
        names = {
            AmazonDomain.US: "美国站",
            AmazonDomain.JP: "日本站",
            AmazonDomain.UK: "英国站",
            AmazonDomain.DE: "德国站",
            AmazonDomain.FR: "法国站",
            AmazonDomain.IT: "意大利站",
            AmazonDomain.ES: "西班牙站",
            AmazonDomain.CA: "加拿大站",
            AmazonDomain.IN: "印度站",
            AmazonDomain.AU: "澳大利亚站",
        }
        return names.get(self, self.value)


class RankingPeriod(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class StrategyPhase(str, Enum):
    SELECTION = "selection"
    LISTING = "listing"
    TRAFFIC = "traffic"
    CONVERSION = "conversion"
    RETENTION = "retention"
    REVIEW = "review"


class DataSource(str, Enum):
    WEB_SCRAPING = "web_scraping"
    OFFICIAL_API = "official_api"
    THIRD_PARTY_TOOL = "third_party_tool"
    MODEL_ESTIMATION = "model_estimation"