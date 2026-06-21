"""Dependency-light possession estimation shared by sport runners.

Ported from Vincent's soccer implementation (sam_model_vincent c76c85d) and kept
coordinate-system agnostic. Callers choose the possession radius and must label the
result as an estimate unless possession ground truth is available.
"""
from __future__ import annotations

from collections import defaultdict
from math import hypot
from typing import Sequence

Position = Sequence[float]


def _euclidean(a: Position, b: Position) -> float:
    return hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


class PossessionTracker:
    """Estimate player/team possession with temporal switch hysteresis."""

    def __init__(
        self,
        possession_radius: float,
        hysteresis_frames: int = 3,
        switch_margin: float = 0.0,
    ) -> None:
        if possession_radius <= 0:
            raise ValueError("possession_radius must be positive")
        if hysteresis_frames <= 0:
            raise ValueError("hysteresis_frames must be positive")
        if switch_margin < 0:
            raise ValueError("switch_margin must be non-negative")
        self.possession_radius = float(possession_radius)
        self.hysteresis_frames = int(hysteresis_frames)
        self.switch_margin = float(switch_margin)
        self.team_frames: dict[int, int] = defaultdict(int)
        self.player_frames: dict[int, int] = defaultdict(int)
        self.player_team: dict[int, int] = {}
        self.holder_id: int | None = None
        self.holder_team: int | None = None
        self.last_team: int | None = None
        self._candidate_id: int | None = None
        self._candidate_streak = 0

    def update(
        self,
        ball_xy: Position | None,
        players_xy: Sequence[Position],
        tracker_ids: Sequence[int],
        team_ids: Sequence[int],
    ) -> tuple[int | None, int | None]:
        """Process one aligned frame and return estimated holder/player team."""
        lengths = {len(players_xy), len(tracker_ids), len(team_ids)}
        if len(lengths) != 1:
            raise ValueError("players_xy, tracker_ids, and team_ids must align")
        for tracker_id, team_id in zip(tracker_ids, team_ids):
            self.player_team[int(tracker_id)] = int(team_id)

        candidates = []
        if ball_xy is not None:
            candidates = [
                (_euclidean(xy, ball_xy), int(tracker_id), int(team_id))
                for xy, tracker_id, team_id in zip(players_xy, tracker_ids, team_ids)
            ]
        self._resolve_holder(candidates)
        self._accumulate()
        return self.current_holder()

    def _resolve_holder(self, candidates: list[tuple[float, int, int]]) -> None:
        if not candidates:
            self._release_holder()
            return
        candidates.sort(key=lambda candidate: candidate[0])
        nearest_dist, nearest_id, nearest_team = candidates[0]
        if nearest_dist > self.possession_radius:
            self._release_holder()
            return
        if nearest_id == self.holder_id:
            self.holder_team = nearest_team
            self.last_team = nearest_team
            self._reset_candidate()
            return

        if self._candidate_id == nearest_id:
            self._candidate_streak += 1
        else:
            self._candidate_id = nearest_id
            self._candidate_streak = 1

        holder_dist = self._holder_distance(candidates)
        decisive = (
            self.holder_id is None
            or holder_dist is None
            or holder_dist > self.possession_radius
            or nearest_dist < holder_dist - self.switch_margin
        )
        if decisive or self._candidate_streak >= self.hysteresis_frames:
            self.holder_id = nearest_id
            self.holder_team = nearest_team
            self.last_team = nearest_team
            self._reset_candidate()

    def _holder_distance(self, candidates: list[tuple[float, int, int]]) -> float | None:
        for distance, tracker_id, _team_id in candidates:
            if tracker_id == self.holder_id:
                return distance
        return None

    def _release_holder(self) -> None:
        self.holder_id = None
        self._reset_candidate()

    def _reset_candidate(self) -> None:
        self._candidate_id = None
        self._candidate_streak = 0

    def _accumulate(self) -> None:
        credited_team = self.holder_team if self.holder_id is not None else self.last_team
        if credited_team is not None:
            self.team_frames[credited_team] += 1
        if self.holder_id is not None:
            self.player_frames[self.holder_id] += 1

    def current_holder(self) -> tuple[int | None, int | None]:
        return self.holder_id, self.holder_team

    def get_team_possession(self) -> dict[str, float | int]:
        """Return two-team credited frame counts and percentages."""
        team_0 = self.team_frames.get(0, 0)
        team_1 = self.team_frames.get(1, 0)
        total = team_0 + team_1
        pct_0 = 100.0 * team_0 / total if total else 0.0
        pct_1 = 100.0 * team_1 / total if total else 0.0
        return {
            "team_0_frames": team_0,
            "team_1_frames": team_1,
            "team_0_pct": pct_0,
            "team_1_pct": pct_1,
        }

    def get_player_possession(self) -> dict[int, dict[str, float | int]]:
        """Return individually credited frame counts and percentages."""
        total = sum(self.player_frames.values())
        return {
            tracker_id: {
                "frames": frames,
                "pct": 100.0 * frames / total if total else 0.0,
                "team": self.player_team.get(tracker_id, -1),
            }
            for tracker_id, frames in self.player_frames.items()
        }
