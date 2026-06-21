"""Possession tracking for the soccer pipeline.

This module is intentionally dependency-light: it relies only on the Python
standard library (``math``/``collections``).  It happily accepts ``numpy``
arrays as input (they are simply iterated/indexed), but it does not import any
heavy ML/CV dependency (``torch``/``cv2``/``ultralytics``/``supervision``).
That keeps the possession math fully unit-testable in isolation and cheap to
run every frame.

All distances are expected in *pitch* units.  ``SoccerPitchConfiguration``
expresses the pitch in centimetres (width 7000 cm = 70 m, length 12000 cm =
120 m), so the default possession radius below is expressed in centimetres.
"""

from collections import defaultdict
from math import hypot
from typing import Dict, List, Optional, Sequence, Tuple

# A "position" is anything indexable yielding two numbers (numpy row, tuple...).
Position = Sequence[float]


def _euclidean(a: Position, b: Position) -> float:
    """Euclidean distance between two 2D points (pure Python, numpy-safe)."""
    return hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


class PossessionTracker:
    """Track ball possession per-player and per-team with temporal smoothing.

    The tracker is fed, every frame, the ball position, the player positions
    and their ``(tracker_id, team_id)`` pairs.  It decides which player (if
    any) currently controls the ball and accumulates frame-count statistics.

    Possession policy (documented so the behaviour is predictable):

    * A player *controls* the ball when they are the closest player to the ball
      AND within ``possession_radius`` (measured in pitch units).
    * To avoid flicker, the individual-holder credit only transfers to a new
      player once that player has been the controlling candidate for
      ``hysteresis_frames`` consecutive frames -- UNLESS the challenge is
      decisive (no current holder, the current holder left the frame / left the
      radius, or the challenger is closer than the current holder by more than
      ``switch_margin``), in which case the switch happens immediately.
    * When no player is within the radius (loose ball / pass in flight) no
      individual player is credited, but the *last team* to hold the ball keeps
      being credited team-possession frames for continuity.
    * If the ball itself is missing for a frame, we likewise keep crediting the
      last holding team and credit no individual.
    """

    def __init__(
        self,
        possession_radius: float = 200.0,
        hysteresis_frames: int = 3,
        switch_margin: float = 50.0,
    ) -> None:
        """
        Args:
            possession_radius: Max player-to-ball distance (pitch units) for a
                player to be considered in control. ~200 cm (2 m) by default.
            hysteresis_frames: Consecutive frames a challenger must be the
                closest in-radius player before a (non-decisive) switch.
            switch_margin: Distance (pitch units) by which a challenger must
                beat the current holder to trigger an immediate switch.
        """
        self.possession_radius = float(possession_radius)
        self.hysteresis_frames = int(hysteresis_frames)
        self.switch_margin = float(switch_margin)

        # Accumulated statistics.
        self.team_frames: Dict[int, int] = defaultdict(int)
        self.player_frames: Dict[int, int] = defaultdict(int)
        self.player_team: Dict[int, int] = {}

        # Current state.
        self.holder_id: Optional[int] = None
        self.holder_team: Optional[int] = None
        self.last_team: Optional[int] = None

        # Hysteresis bookkeeping.
        self._candidate_id: Optional[int] = None
        self._candidate_streak: int = 0

    def update(
        self,
        ball_xy: Optional[Position],
        players_xy: Sequence[Position],
        tracker_ids: Sequence[int],
        team_ids: Sequence[int],
    ) -> Tuple[Optional[int], Optional[int]]:
        """Process one frame and return the current ``(holder_id, holder_team)``.

        Args:
            ball_xy: Ball position in pitch units, or ``None`` if the ball was
                not available this frame.
            players_xy: Sequence of player positions in pitch units, aligned
                with ``tracker_ids`` and ``team_ids``.
            tracker_ids: Per-player ByteTrack ids.
            team_ids: Per-player team ids (expected 0 or 1).

        Returns:
            Tuple ``(holder_id, holder_team)`` after applying the policy. Either
            element may be ``None`` (loose ball / no team yet).
        """
        # Keep the latest known team for every tracked player (used for stats).
        for tracker_id, team_id in zip(tracker_ids, team_ids):
            self.player_team[int(tracker_id)] = int(team_id)

        # Build the list of (distance, tracker_id, team_id) candidates.
        candidates: List[Tuple[float, int, int]] = []
        if ball_xy is not None:
            for xy, tracker_id, team_id in zip(players_xy, tracker_ids, team_ids):
                candidates.append(
                    (_euclidean(xy, ball_xy), int(tracker_id), int(team_id))
                )

        self._resolve_holder(candidates)
        self._accumulate()
        return self.holder_id, self.holder_team

    def _resolve_holder(self, candidates: List[Tuple[float, int, int]]) -> None:
        """Apply the possession + hysteresis policy. Pure Python (testable)."""
        # No ball or no players -> loose ball, keep last team, drop individual.
        if not candidates:
            self.holder_id = None
            self._candidate_id = None
            self._candidate_streak = 0
            return

        candidates.sort(key=lambda c: c[0])
        nearest_dist, nearest_id, nearest_team = candidates[0]

        # Closest player is still outside the possession radius -> loose ball.
        if nearest_dist > self.possession_radius:
            self.holder_id = None
            self._candidate_id = None
            self._candidate_streak = 0
            return

        # The closest in-radius player is already the holder -> confirm/refresh.
        if nearest_id == self.holder_id:
            self.holder_team = nearest_team
            self.last_team = nearest_team
            self._candidate_id = None
            self._candidate_streak = 0
            return

        # A different player is closest in radius -> challenger logic.
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
            self._candidate_id = None
            self._candidate_streak = 0

    def _holder_distance(
        self, candidates: List[Tuple[float, int, int]]
    ) -> Optional[float]:
        """Current ball distance of the existing holder, if present this frame."""
        if self.holder_id is None:
            return None
        for dist, tracker_id, _ in candidates:
            if tracker_id == self.holder_id:
                return dist
        return None

    def _accumulate(self) -> None:
        """Credit one frame to the appropriate team and/or player."""
        # Team continuity: credit the holder's team, else the last holding team.
        credited_team = self.holder_team if self.holder_id is not None else self.last_team
        if credited_team is not None:
            self.team_frames[credited_team] += 1
        # Only credit an individual when an individual is actually in control.
        if self.holder_id is not None:
            self.player_frames[self.holder_id] += 1

    def current_holder(self) -> Tuple[Optional[int], Optional[int]]:
        """Return the current ``(holder_id, holder_team)``."""
        return self.holder_id, self.holder_team

    def get_team_possession(self) -> Dict[str, float]:
        """Return per-team possession frame counts and percentages.

        Percentages are relative to total credited team frames (team0 + team1)
        and sum to 100 when any possession has been recorded.
        """
        team_0 = self.team_frames.get(0, 0)
        team_1 = self.team_frames.get(1, 0)
        total = team_0 + team_1
        if total == 0:
            pct_0 = pct_1 = 0.0
        else:
            pct_0 = 100.0 * team_0 / total
            pct_1 = 100.0 * team_1 / total
        return {
            "team_0_frames": team_0,
            "team_1_frames": team_1,
            "team_0_pct": pct_0,
            "team_1_pct": pct_1,
        }

    def get_player_possession(self) -> Dict[int, Dict[str, float]]:
        """Return per-player possession counts/percentages keyed by tracker id.

        Per-player percentage is relative to the total of all individually
        credited frames (frames where some player was in clear control).
        """
        total = sum(self.player_frames.values())
        result: Dict[int, Dict[str, float]] = {}
        for tracker_id, frames in self.player_frames.items():
            result[tracker_id] = {
                "frames": frames,
                "pct": (100.0 * frames / total) if total else 0.0,
                "team": self.player_team.get(tracker_id, -1),
            }
        return result
