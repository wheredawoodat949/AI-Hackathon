# Evidence-backed tracking health

The basketball runner includes a local `TrackingHealthAgent` fed by the same frame
summaries sent to Arize. It produces an auditable JSON report with:

- observed frame/detection/track counts;
- mean detector confidence;
- mean and maximum frame-to-frame track-set churn;
- rolling threshold events with the exact window, value, and threshold;
- a short factual narrative.

Set an output path in `.env`:

```dotenv
TRACKING_ANALYSIS_OUTPUT=outputs/basketball_tracking_health.json
```

Run any basketball mode normally. The report is written when the video generator
closes, including when Redis and Arize are disabled.

## Interpretation boundary

Track-set churn is:

```text
(new track IDs + lost track IDs) / IDs present in either adjacent frame
```

It is measurable from ByteTrack output, but it is not an ID-swap rate. Players may
enter or leave the view, and tracker fragmentation may create new IDs. A true swap
rate requires identity ground truth or a separately validated association. The agent
therefore says when churn is high and lists plausible categories, but does not select
a cause.

Likewise, simultaneous low confidence and high churn is reported as coincidence, not
causation. Cross-sport or baseline drift claims require two real reports; no baseline
or comparison number is embedded in the code.
