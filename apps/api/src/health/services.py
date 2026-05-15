from datetime import datetime, timezone
from decimal import Decimal
from time import time as time_timestamp
from typing import Annotated

from peewee import JOIN, Case, fn
from wireup import Inject, injectable

from src.domains.entities import Domain, DomainCertificate
from src.domains.enums import DomainCertificateStatus
from src.health.entities import (
    DiskUtilization,
    DiskUtilizationSummary,
    NginxValidationSnapshot,
)


@injectable
class HealthService:
    def __init__(
        self,
        stale_after_seconds: Annotated[int, Inject(config='DISK_UTILIZATION_STALE_AFTER_SECONDS')],
        warning_percent: Annotated[int, Inject(config='DISK_UTILIZATION_WARNING_PERCENT')],
        critical_percent: Annotated[int, Inject(config='DISK_UTILIZATION_CRITICAL_PERCENT')],
        certificate_warning_days: Annotated[int, Inject(config='BANGI_CERTIFICATE_WARNING_DAYS')],
        certificate_error_days: Annotated[int, Inject(config='BANGI_CERTIFICATE_ERROR_DAYS')],
    ):
        self.stale_after_seconds = stale_after_seconds
        self.warning_percent = warning_percent
        self.critical_percent = critical_percent
        self.certificate_warning_days = certificate_warning_days
        self.certificate_error_days = certificate_error_days

    def ingest_disk_utilization(
        self,
        filesystem: str,
        mountpoint: str,
        total_bytes: int,
        used_bytes: int,
        available_bytes: int,
        used_percent: Decimal,
    ) -> DiskUtilization:
        snapshot = DiskUtilization(
            filesystem=filesystem,
            mountpoint=mountpoint,
            total_bytes=total_bytes,
            used_bytes=used_bytes,
            available_bytes=available_bytes,
            used_percent=used_percent,
        )
        snapshot.save()
        return snapshot

    def disk_utilization_history(self, *, days: int) -> tuple[DiskUtilizationSummary, list[DiskUtilization]]:
        now_timestamp = int(time_timestamp())
        history_start_timestamp = now_timestamp - days * 24 * 60 * 60

        date = fn.date(fn.from_unixtime(DiskUtilization.created_at)).alias('date')
        rows = list(
            DiskUtilization.select(
                date,
                fn.max(DiskUtilization.total_bytes),
                fn.avg(DiskUtilization.used_bytes),
                fn.avg(DiskUtilization.available_bytes),
            )
            .where(DiskUtilization.created_at >= history_start_timestamp)
            .group_by(date)
            .order_by(DiskUtilization.created_at.asc())
            .dicts()
        )
        latest_snapshot = DiskUtilization.select().order_by(DiskUtilization.id.desc()).first()

        if latest_snapshot is None:
            return (
                DiskUtilizationSummary(
                    stale=False,
                    severity=None,
                    filesystem=None,
                    mountpoint=None,
                    total_bytes=None,
                    used_bytes=None,
                    available_bytes=None,
                    used_percent=None,
                    last_received_at=None,
                ),
                [],
            )

        latest_received_at = int(latest_snapshot.created_at.timestamp())
        stale = now_timestamp - latest_received_at >= self.stale_after_seconds

        if latest_snapshot.used_percent >= self.critical_percent:
            severity = 'critical'
        elif latest_snapshot.used_percent >= self.warning_percent:
            severity = 'warning'
        else:
            severity = 'normal'

        return (
            DiskUtilizationSummary(
                stale=stale,
                severity=severity,
                filesystem=latest_snapshot.filesystem,
                mountpoint=latest_snapshot.mountpoint,
                total_bytes=latest_snapshot.total_bytes,
                used_bytes=latest_snapshot.used_bytes,
                available_bytes=latest_snapshot.available_bytes,
                used_percent=float(latest_snapshot.used_percent),
                last_received_at=latest_received_at,
            ),
            rows,
        )

    def latest_disk_utilization_summary(self) -> DiskUtilizationSummary:
        latest_snapshot = (
            DiskUtilization.select().order_by(DiskUtilization.created_at.desc(), DiskUtilization.id.desc()).first()
        )
        if latest_snapshot is None:
            return DiskUtilizationSummary(
                stale=False,
                severity=None,
                filesystem=None,
                mountpoint=None,
                total_bytes=None,
                used_bytes=None,
                available_bytes=None,
                used_percent=None,
                last_received_at=None,
            )

        now_timestamp = int(time_timestamp())
        latest_received_at = int(latest_snapshot.created_at.timestamp())
        stale = now_timestamp - latest_received_at >= self.stale_after_seconds

        if latest_snapshot.used_percent >= self.critical_percent:
            severity = 'critical'
        elif latest_snapshot.used_percent >= self.warning_percent:
            severity = 'warning'
        else:
            severity = 'normal'

        return DiskUtilizationSummary(
            stale=stale,
            severity=severity,
            filesystem=latest_snapshot.filesystem,
            mountpoint=latest_snapshot.mountpoint,
            total_bytes=latest_snapshot.total_bytes,
            used_bytes=latest_snapshot.used_bytes,
            available_bytes=latest_snapshot.available_bytes,
            used_percent=float(latest_snapshot.used_percent),
            last_received_at=latest_received_at,
        )

    def record_nginx_validation_snapshot(
        self,
        *,
        domain_id: int | None,
        validation_status: str,
        validation_error: str | None,
        sites_available_files: list[str],
        sites_enabled_refs: list[str],
    ) -> NginxValidationSnapshot:
        snapshot = NginxValidationSnapshot(
            created_at=datetime.now(timezone.utc),
            domain_id=domain_id,
            validation_status=validation_status,
            validation_error=validation_error,
            sites_available_files=sites_available_files,
            sites_enabled_refs=sites_enabled_refs,
        )
        snapshot.save()
        return snapshot

    def latest_nginx_validation_snapshot(self) -> NginxValidationSnapshot | None:
        snapshot = (
            NginxValidationSnapshot.select()
            .order_by(NginxValidationSnapshot.created_at.desc(), NginxValidationSnapshot.id.desc())
            .first()
        )
        if snapshot is None:
            return None

        return snapshot

    def certificate_diagnostics(self) -> list[dict]:
        now = int(time_timestamp())
        status_priority = Case(
            None,
            (
                (DomainCertificate.status == DomainCertificateStatus.expired.value, 0),
                (DomainCertificate.expires_at <= now, 0),
                (DomainCertificate.status == DomainCertificateStatus.failed.value, 1),
                (DomainCertificate.id.is_null(True), 2),
            ),
            3,
        )

        return list(
            Domain.select(
                Domain.id.alias('domain_id'),
                Domain.hostname,
                Domain.is_a_record_set,
                DomainCertificate.id.alias('certificate_id'),
                DomainCertificate.status,
                DomainCertificate.expires_at,
                DomainCertificate.last_attempted_at,
                DomainCertificate.last_issued_at,
                DomainCertificate.failure_count,
                DomainCertificate.failure_reason,
            )
            .join(DomainCertificate, JOIN.LEFT_OUTER)
            .where(
                (Domain.is_disabled == False)
                & (
                    (Domain.is_a_record_set != True)
                    | DomainCertificate.id.is_null(True)
                    | (DomainCertificate.status == DomainCertificateStatus.failed.value)
                    | (DomainCertificate.status == DomainCertificateStatus.expired.value)
                    | (DomainCertificate.expires_at <= now)
                )
            )
            .order_by(status_priority.asc(), Domain.hostname.asc())
            .dicts()
        )
