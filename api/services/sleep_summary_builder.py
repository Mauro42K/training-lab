from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from uuid import UUID

from api.repositories.daily_domains_repository import DailySleepSummaryUpsert
from api.services.daily_domain_rules import APPLE_HEALTH_PROVIDER, resolve_primary_device_name
from api.services.local_date import resolve_local_datetime

_MERGE_GAP = timedelta(minutes=30)
_MAIN_SLEEP_MIN = timedelta(hours=3)
_MAIN_SLEEP_FALLBACK_MIN = timedelta(minutes=90)
_NAP_MIN = timedelta(minutes=20)
_NAP_MAX = timedelta(minutes=180)


@dataclass(frozen=True)
class _LocalizedSleepSession:
    start_local: datetime
    end_local: datetime
    source_bundle_id: str | None
    source_count: int
    has_mixed_sources: bool
    primary_device_name: str | None

    @property
    def duration(self) -> timedelta:
        return self.end_local - self.start_local


@dataclass(frozen=True)
class _MergedSleepBlock:
    start_local: datetime
    end_local: datetime
    source_bundle_ids: tuple[str, ...]
    source_count: int
    has_mixed_sources: bool
    primary_device_names: tuple[str, ...]

    @property
    def duration(self) -> timedelta:
        return self.end_local - self.start_local


class SleepSummaryBuilder:
    def build_rows_for_dates(
        self,
        *,
        user_id: UUID,
        dates: set[date],
        sleep_sessions: list[Any],
        user_timezone: str | None,
        fallback_timezone: str,
    ) -> list[DailySleepSummaryUpsert]:
        rows: list[DailySleepSummaryUpsert] = []
        for target_date in sorted(dates):
            localized = self._localize_sessions(
                sleep_sessions=sleep_sessions,
                user_timezone=user_timezone,
                fallback_timezone=fallback_timezone,
                target_date=target_date,
            )
            if not localized:
                continue

            merged_blocks = self._merge_sessions(localized)
            summary_row = self._build_row_for_target_date(
                user_id=user_id,
                target_date=target_date,
                merged_blocks=merged_blocks,
            )
            if summary_row is not None:
                rows.append(summary_row)
        return rows

    def _localize_sessions(
        self,
        *,
        sleep_sessions: list[Any],
        user_timezone: str | None,
        fallback_timezone: str,
        target_date: date,
    ) -> list[_LocalizedSleepSession]:
        localized: list[_LocalizedSleepSession] = []

        for session in sleep_sessions:
            start_local = resolve_local_datetime(
                instant=session.start_at,
                user_timezone=user_timezone,
                fallback_timezone=fallback_timezone,
            )
            end_local = resolve_local_datetime(
                instant=session.end_at,
                user_timezone=user_timezone,
                fallback_timezone=fallback_timezone,
            )
            tzinfo = end_local.tzinfo
            window_start = datetime.combine(
                target_date - timedelta(days=1),
                time(18, 0),
                tzinfo=tzinfo,
            )
            window_end = datetime.combine(
                target_date,
                time(23, 59, 59),
                tzinfo=tzinfo,
            )
            if end_local < window_start or start_local > window_end:
                continue
            localized.append(
                _LocalizedSleepSession(
                    start_local=start_local,
                    end_local=end_local,
                    source_bundle_id=getattr(session, "source_bundle_id", None),
                    source_count=getattr(session, "source_count", 1),
                    has_mixed_sources=getattr(session, "has_mixed_sources", False),
                    primary_device_name=getattr(session, "primary_device_name", None),
                )
            )

        return sorted(localized, key=lambda item: item.start_local)

    def _merge_sessions(self, sessions: list[_LocalizedSleepSession]) -> list[_MergedSleepBlock]:
        if not sessions:
            return []

        merged: list[_MergedSleepBlock] = []
        current = sessions[0]
        current_start = current.start_local
        current_end = current.end_local
        current_source_bundle_ids = {
            current.source_bundle_id
        } if current.source_bundle_id else set()
        current_source_count = current.source_count
        current_has_mixed_sources = current.has_mixed_sources
        current_primary_device_names = {
            current.primary_device_name
        } if current.primary_device_name else set()

        for session in sessions[1:]:
            gap = session.start_local - current_end
            if gap <= _MERGE_GAP:
                current_end = max(current_end, session.end_local)
                if session.source_bundle_id:
                    current_source_bundle_ids.add(session.source_bundle_id)
                current_source_count = max(current_source_count, session.source_count)
                current_has_mixed_sources = current_has_mixed_sources or session.has_mixed_sources
                if session.primary_device_name:
                    current_primary_device_names.add(session.primary_device_name)
                continue

            merged.append(
                _MergedSleepBlock(
                    start_local=current_start,
                    end_local=current_end,
                    source_bundle_ids=tuple(sorted(current_source_bundle_ids)),
                    source_count=max(current_source_count, len(current_source_bundle_ids) or 1),
                    has_mixed_sources=current_has_mixed_sources or len(current_source_bundle_ids) > 1,
                    primary_device_names=tuple(sorted(current_primary_device_names)),
                )
            )
            current_start = session.start_local
            current_end = session.end_local
            current_source_bundle_ids = {session.source_bundle_id} if session.source_bundle_id else set()
            current_source_count = session.source_count
            current_has_mixed_sources = session.has_mixed_sources
            current_primary_device_names = {session.primary_device_name} if session.primary_device_name else set()

        merged.append(
            _MergedSleepBlock(
                start_local=current_start,
                end_local=current_end,
                source_bundle_ids=tuple(sorted(current_source_bundle_ids)),
                source_count=max(current_source_count, len(current_source_bundle_ids) or 1),
                has_mixed_sources=current_has_mixed_sources or len(current_source_bundle_ids) > 1,
                primary_device_names=tuple(sorted(current_primary_device_names)),
            )
        )
        return merged

    def _build_row_for_target_date(
        self,
        *,
        user_id: UUID,
        target_date: date,
        merged_blocks: list[_MergedSleepBlock],
    ) -> DailySleepSummaryUpsert | None:
        main_candidates = [
            block
            for block in merged_blocks
            if block.end_local.date() == target_date and time(3, 0) <= block.end_local.time() <= time(15, 0)
        ]
        complete_candidates = [block for block in main_candidates if block.duration >= _MAIN_SLEEP_MIN]
        partial_candidates = [block for block in main_candidates if block.duration >= _MAIN_SLEEP_FALLBACK_MIN]

        completeness_status: str | None = None
        if complete_candidates:
            main_sleep = self._select_main_sleep(complete_candidates)
            completeness_status = "complete"
        elif partial_candidates:
            main_sleep = self._select_main_sleep(partial_candidates)
            completeness_status = "partial"
        else:
            return None

        nap_blocks = [
            block
            for block in merged_blocks
            if block != main_sleep
            and block.start_local.date() == target_date
            and time(9, 0) <= block.start_local.time() <= time(21, 0)
            and _NAP_MIN <= block.duration < _NAP_MAX
        ]

        total_sleep_sec = int(sum(block.duration.total_seconds() for block in merged_blocks))
        naps_total_sleep_sec = int(sum(block.duration.total_seconds() for block in nap_blocks))
        source_bundle_ids = {
            source_bundle_id
            for block in merged_blocks
            for source_bundle_id in block.source_bundle_ids
        }
        primary_device_name = resolve_primary_device_name(
            [
                device_name
                for block in merged_blocks
                for device_name in block.primary_device_names
            ]
        )

        return DailySleepSummaryUpsert(
            user_id=user_id,
            local_date=target_date,
            total_sleep_sec=total_sleep_sec,
            # Persist summary instants as UTC while still selecting main sleep in local time.
            main_sleep_start_at=main_sleep.start_local.astimezone(UTC),
            main_sleep_end_at=main_sleep.end_local.astimezone(UTC),
            main_sleep_duration_sec=int(main_sleep.duration.total_seconds()),
            naps_count=len(nap_blocks),
            naps_total_sleep_sec=naps_total_sleep_sec,
            completeness_status=completeness_status,
            provider=APPLE_HEALTH_PROVIDER,
            source_count=max(
                max((block.source_count for block in merged_blocks), default=1),
                len(source_bundle_ids) or 1,
            ),
            has_mixed_sources=any(block.has_mixed_sources for block in merged_blocks) or len(source_bundle_ids) > 1,
            primary_device_name=primary_device_name,
        )

    def _select_main_sleep(self, candidates: list[_MergedSleepBlock]) -> _MergedSleepBlock:
        return max(candidates, key=lambda block: (block.duration, block.end_local))
