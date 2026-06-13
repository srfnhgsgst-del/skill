from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ecommerce_ops_skill.platform import Platform, AmazonDomain, RankingPeriod, DataSource


@dataclass
class RankingItem:
    platform: Platform
    rank: int
    asin_or_id: str
    title: str
    price: Optional[float] = None
    currency: str = "USD"
    rating: Optional[float] = None
    review_count: Optional[int] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    is_sponsored: bool = False
    is_bestseller: bool = False
    is_amazon_choice: bool = False
    data_source: DataSource = DataSource.WEB_SCRAPING
    fetched_at: datetime = field(default_factory=datetime.now)


@dataclass
class BSRHistory:
    asin: str
    category: str
    rank: int
    timestamp: datetime


@dataclass
class ProductDetail:
    platform: Platform
    asin_or_id: str
    title: str
    brand: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    currency: str = "USD"
    rating: Optional[float] = None
    review_count: Optional[int] = None
    bsr: Optional[int] = None
    bsr_category: Optional[str] = None
    buy_box_owner: Optional[str] = None
    availability: str = "unknown"
    seller_type: Optional[str] = None
    dimensions: Optional[str] = None
    weight: Optional[str] = None
    first_available: Optional[datetime] = None
    images: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    description: Optional[str] = None
    variations: list[dict] = field(default_factory=list)
    data_source: DataSource = DataSource.WEB_SCRAPING
    fetched_at: datetime = field(default_factory=datetime.now)


@dataclass
class CategoryNode:
    id: str
    name: str
    platform: Platform
    parent_id: Optional[str] = None
    product_count: Optional[int] = None
    children: list["CategoryNode"] = field(default_factory=list)


@dataclass
class BestSellerList:
    platform: Platform
    category_id: str
    category_name: str
    amazon_domain: Optional[AmazonDomain] = None
    items: list[RankingItem] = field(default_factory=list)
    period: RankingPeriod = RankingPeriod.HOURLY
    total_items: int = 100
    fetched_at: datetime = field(default_factory=datetime.now)


@dataclass
class SalesEstimate:
    asin: str
    platform: Platform
    estimated_daily_sales: Optional[int] = None
    estimated_monthly_sales: Optional[int] = None
    estimated_monthly_revenue: Optional[float] = None
    sales_rank_30d: Optional[int] = None
    sales_rank_90d: Optional[int] = None
    sales_trend: Optional[str] = None
    confidence_level: float = 0.0
    estimation_method: str = "bsr_correlation"
    data_source: DataSource = DataSource.MODEL_ESTIMATION


@dataclass
class KeywordData:
    keyword: str
    platform: Platform
    search_volume: Optional[int] = None
    search_volume_trend: Optional[str] = None
    competition_level: Optional[str] = None
    cpc_bid: Optional[float] = None
    related_keywords: list[str] = field(default_factory=list)


@dataclass
class StrategyAdvice:
    phase: str
    platform: Platform
    title: str
    description: str
    priority: int = 3
    actionable_steps: list[str] = field(default_factory=list)
    expected_impact: Optional[str] = None
    difficulty: Optional[str] = None


@dataclass
class CompetitorSnapshot:
    asin_or_id: str
    platform: Platform
    title: str
    price: Optional[float] = None
    bsr: Optional[int] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    estimated_monthly_sales: Optional[int] = None
    main_keywords: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)