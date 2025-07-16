from wireup import service

from src.tracker.entities import TrackClick


@service
class TrackClickService:
    def track(
        self, click_id: str, campaign_name: str | None, adset_name: str | None, ad_name: str | None, pixel: str | None
    ) -> None:
        click = TrackClick(
            click_id=click_id, campaign_name=campaign_name, adset_name=adset_name, ad_name=ad_name, pixel=pixel
        )
        click.save()
