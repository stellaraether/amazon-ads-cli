"""Amazon Ads API client wrapper."""

from ad_api.api import reports, sponsored_products
from ad_api.base import Marketplaces


class AdsAPIError(Exception):
    """Raised when the Ads API returns an error."""

    def __init__(self, message, response_body=None):
        super().__init__(message)
        self.response_body = response_body


class AdsAPIClient:
    """Client for Amazon Advertising API v3."""

    def __init__(self, credentials):
        self.credentials = credentials
        self.marketplace = Marketplaces.NA

    def list_campaigns(self, body=None):
        """List campaigns."""
        body = body or {}
        return sponsored_products.CampaignsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).list_campaigns(body=body)

    def edit_campaigns(self, body):
        """Edit campaigns."""
        return sponsored_products.CampaignsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).edit_campaigns(body=body)

    def create_campaigns(self, body):
        """Create campaigns."""
        return sponsored_products.CampaignsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).create_campaigns(body=body)

    def list_ad_groups(self, body=None):
        """List ad groups."""
        body = body or {}
        return sponsored_products.AdGroupsV3(marketplace=self.marketplace, credentials=self.credentials).list_ad_groups(
            body=body
        )

    def create_ad_groups(self, body):
        """Create ad groups, returning the created objects."""
        return sponsored_products.AdGroupsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).create_ad_groups(body=body, prefer=True)

    def edit_ad_groups(self, body):
        """Edit ad groups, returning the updated objects."""
        return sponsored_products.AdGroupsV3(marketplace=self.marketplace, credentials=self.credentials).edit_ad_groups(
            body=body, prefer=True
        )

    def delete_ad_groups(self, body):
        """Delete ad groups."""
        return sponsored_products.AdGroupsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).delete_ad_groups(body=body)

    def list_product_ads(self, body=None):
        """List product ads."""
        body = body or {}
        return sponsored_products.ProductAdsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).list_product_ads(body=body)

    def create_product_ads(self, body):
        """Create product ads, returning the created objects."""
        return sponsored_products.ProductAdsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).create_product_ads(body=body, prefer=True)

    def edit_product_ads(self, body):
        """Edit product ads, returning the updated objects."""
        return sponsored_products.ProductAdsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).edit_product_ads(body=body, prefer=True)

    def delete_product_ads(self, body):
        """Delete product ads."""
        return sponsored_products.ProductAdsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).delete_product_ads(body=body)

    def list_keywords(self, body=None):
        """List keywords."""
        body = body or {}
        return sponsored_products.KeywordsV3(marketplace=self.marketplace, credentials=self.credentials).list_keywords(
            body=body
        )

    def create_keyword(self, body):
        """Create a keyword."""
        return sponsored_products.KeywordsV3(marketplace=self.marketplace, credentials=self.credentials).create_keyword(
            body=body
        )

    def edit_keyword(self, keyword_id, body):
        """Edit a keyword."""
        return sponsored_products.KeywordsV3(marketplace=self.marketplace, credentials=self.credentials).edit_keyword(
            keywordId=keyword_id, body=body
        )

    def list_negative_keywords(self, body=None):
        """List negative keywords."""
        body = body or {}
        return sponsored_products.NegativeKeywordsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).list_negative_keywords(body=body)

    def create_negative_keyword(self, body):
        """Create a negative keyword."""
        return sponsored_products.NegativeKeywordsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).create_negative_keyword(body=body)

    def delete_negative_keywords(self, body):
        """Delete negative keywords."""
        return sponsored_products.NegativeKeywordsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).delete_negative_keywords(body=body)

    def list_negative_product_targets(self, body=None):
        """List negative product targets."""
        body = body or {}
        return sponsored_products.NegativeTargetsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).list_negative_product_targets(body=body)

    def create_negative_product_targets(self, body):
        """Create negative product targets."""
        return sponsored_products.NegativeTargetsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).create_negative_product_targets(body=body)

    def delete_negative_product_targets(self, body):
        """Delete negative product targets."""
        return sponsored_products.NegativeTargetsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).delete_negative_product_targets(body=body)

    def list_product_targets(self, body=None):
        """List product targets."""
        body = body or {}
        return sponsored_products.TargetsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).list_product_targets(body=body)

    def create_product_targets(self, body):
        """Create product targets."""
        return sponsored_products.TargetsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).create_product_targets(body=body)

    def edit_product_targets(self, body):
        """Edit product targets."""
        return sponsored_products.TargetsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).edit_product_targets(body=body)

    def delete_product_targets(self, body):
        """Delete product targets."""
        return sponsored_products.TargetsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).delete_product_targets(body=body)

    def get_targeting_bid_recommendations(self, body):
        """Get theme-based bid recommendations for targeting expressions."""
        return sponsored_products.BidRecommendationsV3(
            marketplace=self.marketplace, credentials=self.credentials
        ).get_bid_recommendations(body=body)

    def post_report(self, body):
        """Submit a report request."""
        return reports.Reports(marketplace=self.marketplace, credentials=self.credentials).post_report(body=body)

    def get_report(self, report_id):
        """Get report status and URL."""
        return reports.Reports(marketplace=self.marketplace, credentials=self.credentials).get_report(
            reportId=report_id
        )
