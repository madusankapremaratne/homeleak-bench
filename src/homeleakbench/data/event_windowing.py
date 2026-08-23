"""Group a session's sensor events into fixed-duration context windows."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class EventWindow:
    window_id: str
    session_id: str
    start: pd.Timestamp
    end: pd.Timestamp
    events: pd.DataFrame = field(repr=False)

    @property
    def resident_ids(self) -> list[str]:
        return sorted(self.events["resident_id"].dropna().unique().tolist())

    @property
    def rooms(self) -> list[str]:
        return sorted(self.events["room"].dropna().unique().tolist())


def build_windows(
    events: pd.DataFrame,
    window_seconds: int,
    stride_seconds: int,
    min_events_per_window: int = 1,
    max_events_per_window: int | None = None,
) -> list[EventWindow]:
    """Slide fixed windows over each session's events independently."""
    windows: list[EventWindow] = []
    stride = pd.Timedelta(seconds=stride_seconds)
    width = pd.Timedelta(seconds=window_seconds)

    for session_id, session_events in events.groupby("session_id", sort=False):
        session_events = session_events.sort_values("timestamp")
        t0 = session_events["timestamp"].min()
        t_end = session_events["timestamp"].max()

        cursor = t0
        idx = 0
        while cursor <= t_end:
            window_end = cursor + width
            mask = (session_events["timestamp"] >= cursor) & (
                session_events["timestamp"] < window_end
            )
            window_events = session_events.loc[mask]

            if len(window_events) >= min_events_per_window:
                if max_events_per_window is not None:
                    window_events = window_events.iloc[:max_events_per_window]
                windows.append(
                    EventWindow(
                        window_id=f"{session_id}-w{idx}",
                        session_id=str(session_id),
                        start=cursor,
                        end=window_end,
                        events=window_events.reset_index(drop=True),
                    )
                )
                idx += 1

            cursor += stride

    return windows
