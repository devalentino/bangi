from wireup import service

from src.tracker.entities import TrackClick


@service
class TrackClickService:
    def track(self, click_id: str, campaign_id: str, parameters: dict) -> None:
        click = TrackClick(click_id=click_id, campaign_id=campaign_id, parameters=parameters)
        click.save()
