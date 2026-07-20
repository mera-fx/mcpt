from __future__ import annotations

from dataclasses import dataclass
import html
from typing import Mapping, Sequence


@dataclass(frozen=True)
class StrategyExplanation:
    title: str
    idea: str
    rules: tuple[tuple[str, str], ...]
    parameters: tuple[tuple[str, str], ...]
    example: str
    distinction: str


STRATEGY_EXPLANATION_CSS = """
.strategy-explanation-section .plain-language-lead {
  max-width: 1080px;
  font-size: 1.04rem;
}
.strategy-rule-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin: 16px 0 20px;
}
.strategy-rule-card,
.strategy-example,
.strategy-distinction {
  background: var(--panel2, var(--panel-2, #152641));
  border: 1px solid var(--line, var(--border, #2b3e5d));
  border-radius: 10px;
  padding: 15px 17px;
}
.strategy-rule-card h3 {
  color: var(--accent, #7dd3fc);
  font-size: .84rem;
  letter-spacing: .04em;
  margin: 0 0 5px;
  text-transform: uppercase;
}
.strategy-rule-card p,
.strategy-example p,
.strategy-distinction p {
  margin: 0;
}
.strategy-parameter-table {
  width: 100%;
  border-collapse: collapse;
  margin: 10px 0 18px;
}
.strategy-parameter-table th,
.strategy-parameter-table td {
  border-bottom: 1px solid var(--line, var(--border, #2b3e5d));
  padding: 9px 10px;
  text-align: left;
  vertical-align: top;
  white-space: normal;
}
.strategy-parameter-table th {
  color: #bfdbfe;
  width: 25%;
}
.strategy-example {
  border-left: 4px solid var(--accent, #7dd3fc);
  margin-top: 14px;
}
.strategy-distinction {
  margin-top: 12px;
}
.strategy-example strong,
.strategy-distinction strong {
  display: block;
  margin-bottom: 5px;
}
@media(max-width: 800px) {
  .strategy-rule-grid { grid-template-columns: 1fr; }
  .strategy-parameter-table th { width: 34%; }
}
"""


def _explanation(
    title: str,
    idea: str,
    rules: Sequence[tuple[str, str]],
    parameters: Sequence[tuple[str, str]],
    example: str,
    distinction: str,
) -> StrategyExplanation:
    return StrategyExplanation(
        title=title,
        idea=idea,
        rules=tuple(rules),
        parameters=tuple(parameters),
        example=example,
        distinction=distinction,
    )


STRATEGY_EXPLANATIONS: Mapping[str, StrategyExplanation] = {
    "EXP-001": _explanation(
        "Hourly Donchian breakout",
        "The strategy follows price breakouts. It stays long after Bitcoin closes "
        "above its recent range and stays short after Bitcoin closes below it.",
        (
            (
                "Setup",
                "On each hourly candle, find the highest and lowest closing prices "
                "from the previous lookback window. The current candle is excluded.",
            ),
            (
                "Entry and direction",
                "A close above the previous upper boundary changes the position to "
                "long. A close below the previous lower boundary changes it to short.",
            ),
            (
                "Holding rule",
                "Between breakouts, the last position is carried forward. The "
                "strategy does not repeatedly enter on every candle.",
            ),
            (
                "Exit",
                "There is no separate price target. An opposite breakout closes and "
                "reverses the existing position.",
            ),
        ),
        (
            (
                "Lookback",
                "How many recent hourly closing prices define the breakout range. "
                "A smaller number reacts faster; a larger number demands a more "
                "substantial breakout.",
            ),
            (
                "Long / short signal",
                "+1 means the strategy benefits from a rise. -1 means it benefits "
                "from a fall.",
            ),
        ),
        "If the highest prior close is 100 and the lowest is 90, a new close at "
        "101 creates a long signal. The strategy remains long until a later close "
        "breaks below the then-current lower boundary.",
        "The channel uses prior closing prices, not the current high and low. The "
        "lookback is a number of hourly candles, not a percentage move.",
    ),
    "EXP-002": _explanation(
        "Hourly z-score mean reversion",
        "The strategy looks for Bitcoin to fall unusually far below its recent "
        "average, then buys in expectation of a recovery toward that average.",
        (
            (
                "Setup",
                "Calculate a rolling average and rolling standard deviation of the "
                "hourly price, then express the current distance from the average "
                "as a z-score.",
            ),
            (
                "Entry",
                "Enter long when the completed candle's z-score falls below the "
                "locked entry threshold. Execution occurs at the next hourly open.",
            ),
            (
                "Stop",
                "This research version is governed by its locked strategy rules; "
                "the principal exit is recovery to the rolling mean rather than a "
                "separate profit target.",
            ),
            (
                "Exit and direction",
                "Exit when price recovers to the rolling mean. The strategy is "
                "long-only and remains flat when no setup exists.",
            ),
        ),
        (
            (
                "Rolling window",
                "The number of hourly candles used to estimate the recent average "
                "and normal variation.",
            ),
            (
                "Entry z-score",
                "How many standard deviations below the average price must fall "
                "before the strategy buys. More negative values demand a rarer drop.",
            ),
        ),
        "If the rolling mean is 100, the standard deviation is 5 and price is 90, "
        "the z-score is (90 - 100) / 5 = -2.0. A -2.0 entry threshold would permit "
        "a long entry, with the rolling mean near 100 acting as the recovery exit.",
        "A z-score of -2 does not mean price fell 2%. It means price is two recent "
        "standard deviations below its rolling average.",
    ),
    "EXP-003": _explanation(
        "Volatility-compression breakout",
        "The strategy waits for an unusually quiet period, then buys when price "
        "breaks above its recent high. The hypothesis is that compressed markets "
        "can expand into directional moves.",
        (
            (
                "Setup",
                "Measure recent realized volatility. A candle counts as compressed "
                "when volatility is within the quietest locked fraction of its "
                "trailing history. A compression must have occurred recently.",
            ),
            (
                "Entry",
                "Enter long when a completed hourly close breaks above the highest "
                "prior high over the breakout lookback. Execute at the next open.",
            ),
            (
                "Stop",
                "Exit if a completed close breaks below the lowest low of the "
                "previous 24 hours.",
            ),
            (
                "Time exit and direction",
                "Exit after a maximum 168-hour hold if the stop has not occurred. "
                "The strategy is long-only.",
            ),
        ),
        (
            (
                "Volatility lookback (48)",
                "The latest 48 hourly returns estimate current volatility.",
            ),
            (
                "Compression quantile (0.20)",
                "Volatility must be in approximately the quietest 20% of its "
                "trailing reference history.",
            ),
            (
                "Breakout lookback (48)",
                "Price must close above the highest high from the prior 48 hours.",
            ),
        ),
        "Suppose current 48-hour volatility is below the trailing 20th percentile "
        "and the highest high from the previous 48 hours is 100. A completed close "
        "at 101 creates a long signal, which enters at the next hourly open.",
        "The 0.20 compression value is a percentile of historical volatility. It "
        "does not mean a 20% price move or a 20% stop.",
    ),
    "EXP-004": _explanation(
        "QQQ opening-range breakout",
        "The strategy uses the first minutes of the New York cash session to define "
        "a range, then trades the first completed breakout from that range.",
        (
            (
                "Setup",
                "Use the opening-range length to record the highest high and lowest "
                "low after 09:30 New York.",
            ),
            (
                "Entry",
                "A completed five-minute close above the range permits a long; a "
                "close below permits a short. Entry occurs at the next five-minute "
                "open.",
            ),
            (
                "Stop",
                "A long stops at the opening-range low. A short stops at the "
                "opening-range high.",
            ),
            (
                "Limits and exit",
                "Take at most one trade per day, allow no reversal, stop accepting "
                "signals at 11:55, and close any open trade at 15:55.",
            ),
        ),
        (
            (
                "Opening-range minutes",
                "How much of the morning establishes the boundaries. The fixed "
                "version used 15 minutes; the small comparison also measured 5 and 30.",
            ),
            (
                "Direction mode",
                "Long, short or both determines which side of the opening range is "
                "eligible to trade.",
            ),
        ),
        "If the opening range is 500 to 502 and a completed five-minute candle "
        "closes at 502.20, a long can enter at the next five-minute open. Its stop "
        "is 500 and it is closed by 15:55 if the stop is never reached.",
        "A wick above the range is not enough. The completed five-minute candle "
        "must close outside, and the trade enters on the next bar to avoid lookahead.",
    ),
    "EXP-005": _explanation(
        "NQ/MNQ 15-minute opening-range breakout",
        "The strategy trades the first confirmed breakout from the Nasdaq futures "
        "cash-session opening range and then holds until the stop or end of day.",
        (
            (
                "Setup",
                "The first three five-minute candles from 09:30 through 09:44:59 "
                "define the fixed opening-range high and low.",
            ),
            (
                "Entry",
                "Take whichever occurs first: a completed close above the range for "
                "a long or below it for a short. Enter at the next five-minute open.",
            ),
            (
                "Stop",
                "A long stops at the opening-range low. A short stops at the "
                "opening-range high.",
            ),
            (
                "Limits and exit",
                "One trade per day, no reversal, final signal at 11:55, latest entry "
                "at 12:00, no profit target, and forced flat at 15:55.",
            ),
        ),
        (
            (
                "15-minute opening range",
                "The high and low of the first three cash-session five-minute bars.",
            ),
            (
                "Final entry time",
                "The last time a new position may begin. It limits late breakouts "
                "without changing the end-of-day exit.",
            ),
        ),
        "If the first 15 minutes create a range from 20,000 to 20,050 and the 10:05 "
        "bar closes at 20,060, the strategy enters long at the 10:10 open. The stop "
        "remains 20,000 and an open trade is closed at 15:55.",
        "There is no fixed profit target in this version. A profitable trade can "
        "continue until 15:55, while its initial risk depends on the full range width.",
    ),
    "EXP-006": _explanation(
        "Opening-range entry-window optimization",
        "This experiment kept the same basic NQ/MNQ opening-range breakout and "
        "compared 27 combinations of range length, final entry time and direction.",
        (
            (
                "Setup",
                "Build a 5-, 15- or 30-minute opening range from the cash-session "
                "high and low.",
            ),
            (
                "Entry",
                "Enter at the next five-minute open after the first eligible "
                "completed close outside the range. Test long-only, short-only and both.",
            ),
            (
                "Stop",
                "A long uses the opening-range low; a short uses the opening-range high.",
            ),
            (
                "Limits and exit",
                "Test final entry cutoffs of 10:30, 11:15 and 12:00. Take one trade "
                "per day, no reversal, no target, and close at 15:55.",
            ),
        ),
        (
            (
                "Opening range: 5 / 15 / 30",
                "A shorter range reacts sooner; a longer range requires more early "
                "session information before a breakout can occur.",
            ),
            (
                "Final entry: 10:30 / 11:15 / 12:00",
                "How late a new breakout may be traded. This is an eligibility "
                "window, not the forced exit time.",
            ),
            (
                "Direction: long / short / both",
                "Which breakout side is allowed. The measured candidate selected "
                "15 minutes, 10:30 and both directions.",
            ),
        ),
        "With a 15-minute range and 10:30 final-entry rule, a breakout confirmed at "
        "10:25 can enter at 10:30. A breakout confirmed at 10:30 cannot enter at "
        "10:35 because the permitted entry window has ended.",
        "The three fractions of the search are separate choices: range duration, "
        "entry-window duration and direction. The optimizer did not create a new "
        "indicator; it compared different operating versions of the same ORB idea.",
    ),
    "EXP-007": _explanation(
        "Fixed 30-minute long-only 1R opening-range breakout",
        "The strategy buys the first confirmed upside breakout from the first "
        "30 minutes, risks the full distance back to the range low, and seeks an "
        "equal-sized profit.",
        (
            (
                "Setup",
                "The six five-minute candles from 09:30 to 09:59:59 define the "
                "opening-range high and low.",
            ),
            (
                "Entry",
                "The first completed five-minute close strictly above the range high "
                "creates a long signal. Enter at the next five-minute open.",
            ),
            (
                "Stop and target",
                "Stop at the opening-range low. Define 1R as entry minus that stop; "
                "the target is entry plus 1R.",
            ),
            (
                "Limits and exit",
                "Long only, one trade per day, last signal at 13:55, flat at 14:00. "
                "One-minute data determines whether stop or target occurs first.",
            ),
        ),
        (
            (
                "30-minute opening range",
                "The first half hour establishes the high and low.",
            ),
            (
                "1R target",
                "The potential reward equals the initial dollar risk. It is a "
                "1-to-1 reward-to-risk target.",
            ),
        ),
        "If the range is 20,000 to 20,100 and entry is 20,120, the stop is 20,000. "
        "Risk is 120 points, so the 1R target is 20,240.",
        "R is the distance between actual entry and stop, not the range width alone "
        "and not a percentage of the account. If stop and target touch in the same "
        "one-minute bar, the test conservatively records the stop first.",
    ),
    "EXP-008": _explanation(
        "Long-only opening-range exit-geometry search",
        "This experiment kept the upside ORB entry concept and compared how opening-"
        "range length, reward target and forced-exit time change its behaviour.",
        (
            (
                "Setup",
                "Build a 15-, 30- or 45-minute opening range from the early "
                "cash-session high and low.",
            ),
            (
                "Entry",
                "Enter long at the next five-minute open after the first completed "
                "close above the opening-range high.",
            ),
            (
                "Stop and target",
                "Stop at the range low. Test profit targets of 0.5R, 1R and 1.5R, "
                "where R is the actual entry-to-stop distance.",
            ),
            (
                "Limits and exit",
                "One trade per day. Test forced exits at 12:00, 14:00 and 15:55. "
                "One-minute data resolves stop and target order.",
            ),
        ),
        (
            (
                "Opening range: 15 / 30 / 45",
                "How much early trading establishes the breakout boundary.",
            ),
            (
                "Target: 0.5R / 1R / 1.5R",
                "Reward as a multiple of initial entry-to-stop risk.",
            ),
            (
                "Forced flat: 12:00 / 14:00 / 15:55",
                "How long an unfinished trade may remain open. The measured candidate "
                "selected 45 minutes, 1.5R and 15:55.",
            ),
        ),
        "If entry is 20,120 and the range-low stop is 20,000, R is 120 points. A "
        "0.5R target is 20,180, a 1R target is 20,240 and a 1.5R target is 20,300.",
        "The decimal target is a multiple of trade risk, not a fraction of the NQ "
        "price. A 1.5R target means potential profit is one-and-a-half times initial risk.",
    ),
    "EXP-009": _explanation(
        "Six-family strategy discovery tournament",
        "This was a broad comparison of six different intraday ideas, with four "
        "locked candidates per family. It measured trade-offs rather than declaring "
        "one automatic winner.",
        (
            (
                "Setup",
                "Measure ORB pullbacks, failed ORB reversals, VWAP mean reversion, "
                "VWAP trend pullbacks, compression breakouts and opening drives.",
            ),
            (
                "Entry",
                "Every family uses completed five-minute information and enters at "
                "the next five-minute open to avoid lookahead.",
            ),
            (
                "Execution",
                "One-minute bars sequence entries, stops and targets. If stop and "
                "target touch in the same minute, the stop is recorded first.",
            ),
            (
                "Comparison",
                "Every candidate uses the same sessions, one-contract sizing, costs "
                "and 15:55 forced flat so differences come from the strategy rules.",
            ),
        ),
        (
            (
                "Four candidates per family",
                "A deliberately small variation budget measured meaningful rule "
                "differences without a large optimization.",
            ),
            (
                "Pareto nondominated",
                "No other measured candidate was clearly better across all chosen "
                "performance, risk and practical dimensions.",
            ),
        ),
        "A high-win-rate candidate could still have smaller winners and a weaker "
        "payoff ratio, while a lower-win-rate candidate could earn more per winner. "
        "The tournament keeps both visible instead of collapsing them into one score.",
        "EXP-009 was discovery, not confirmation. Its comparisons describe what each "
        "strategy did on the shared history; they do not prove that a measured edge is real.",
    ),
    "EXP-010": _explanation(
        "Opening-drive continuation",
        "The strategy asks whether the first 30 minutes produced a genuinely "
        "directional move. If the close travelled far enough from the open relative "
        "to the full opening range, it trades in that direction from 10:00.",
        (
            (
                "Setup",
                "Record the 09:30 open, the high and low from 09:30–10:00, and the "
                "close of the completed 09:55 five-minute bar.",
            ),
            (
                "Direction and entry",
                "A close above the open creates a long direction; below creates a "
                "short direction. If drive fraction passes its threshold, enter at "
                "the 10:00 five-minute open.",
            ),
            (
                "Stop",
                "A long stops at the first-30-minute low. A short stops at the "
                "first-30-minute high.",
            ),
            (
                "Exit",
                "The time-exit version holds until stop or 15:55. The target version "
                "also exits at 1.5R if that target is reached first.",
            ),
        ),
        (
            (
                "Drive fraction: 0.50 or 0.75",
                "Absolute open-to-close movement divided by the full first-30-minute "
                "high-low range. Higher thresholds demand a cleaner directional close.",
            ),
            (
                "Time or 1.5R exit",
                "Time allows a large trend to continue until 15:55. The 1.5R version "
                "takes profit once reward reaches 1.5 times initial risk.",
            ),
        ),
        "Open 20,000; high 20,080; low 19,980; close 20,060. The range is 100 "
        "points and the directional move is 60, so drive fraction = 60 / 100 = "
        "0.60. It passes 0.50 but fails 0.75, and its direction is long.",
        "A 0.50 drive fraction does not mean NQ rose 50%. It means the directional "
        "open-to-close move covered 50% of that morning's total high-low range.",
    ),
}


FAMILY_EXPLANATIONS: Mapping[str, StrategyExplanation] = {
    "orb_pullback_continuation": _explanation(
        "ORB pullback continuation",
        "Wait for an opening-range breakout, then enter only if price retests the "
        "broken boundary and closes back in the breakout direction.",
        (
            ("Setup", "Build a 30-minute opening range and wait for the first completed close outside it."),
            ("Entry", "Within 30 minutes, require a retest of the broken boundary and a close back beyond it; enter next open."),
            ("Stop", "Use the opening-range midpoint as the stop."),
            ("Exit", "Test a 1R or 1.5R target; long-only and both-direction versions were measured."),
        ),
        (
            ("Pullback window", "The breakout gets 30 minutes to produce a valid retest."),
            ("1R / 1.5R", "Profit target as a multiple of entry-to-stop risk."),
        ),
        "After an upside breakout, price trades back to the old range high but "
        "closes above it. That shows a retest rather than an immediate failed breakout.",
        "This does not buy the initial breakout. It deliberately waits for a pullback confirmation.",
    ),
    "failed_orb_reversal": _explanation(
        "Failed ORB reversal",
        "Trade against a breakout that quickly fails and closes back inside the opening range.",
        (
            ("Setup", "Build a 30-minute opening range and record the first completed close outside it."),
            ("Entry", "If price closes back inside within the allowed failure window, enter the reversal at the next open."),
            ("Stop", "Place the stop beyond the extreme reached from breakout through failure."),
            ("Exit", "Test 1R and 1.5R targets with 30- and 60-minute failure windows."),
        ),
        (
            ("Failure window", "How quickly the breakout must return inside to count as failed."),
            ("Reversal", "An upside failure creates a short; a downside failure creates a long."),
        ),
        "Price closes above the opening-range high, then closes back inside 20 minutes later. "
        "The strategy enters short at the next open, expecting the failed breakout to reverse.",
        "It is the opposite hypothesis from breakout continuation: the return inside the range is the signal.",
    ),
    "vwap_mean_reversion": _explanation(
        "VWAP mean reversion",
        "Fade an unusually large extension away from session VWAP after price begins moving back toward it.",
        (
            ("Setup", "After 10:30, measure distance from session VWAP using a 1.5- or 2-standard-deviation band."),
            ("Entry", "Wait for price to move outside the band, then close back inside; enter toward VWAP next open."),
            ("Stop", "Use the most extreme price reached during the excursion."),
            ("Exit", "Exit at VWAP or at a 1R target, depending on the locked candidate."),
        ),
        (
            ("VWAP", "Volume-weighted average price for the current session."),
            ("1.5 / 2 standard deviations", "How unusual the extension must be before a setup can form."),
        ),
        "If price stretches above the upper 2-deviation band and then closes back inside it, "
        "the strategy enters short toward VWAP at the next open.",
        "Touching an outer band is not enough; the completed close back inside is the reversal confirmation.",
    ),
    "vwap_trend_pullback": _explanation(
        "VWAP trend pullback",
        "Join an established intraday trend when price pulls back to VWAP and then confirms the trend is resuming.",
        (
            ("Setup", "After 10:00, define trend from price relative to VWAP and VWAP's slope over three completed bars."),
            ("Entry", "Require a pullback that touches VWAP and closes on the trend side, followed by one or two confirmations."),
            ("Stop", "Place the stop beyond the extreme formed during the pullback and confirmation."),
            ("Exit", "Test a 1R or 1.5R target in the established trend direction."),
        ),
        (
            ("VWAP slope", "Whether session VWAP has risen or fallen across the last three completed bars."),
            ("Confirming closes", "One or two closes required before entry; more confirmation enters later."),
        ),
        "With price above a rising VWAP, a pullback touches VWAP and closes back above it. "
        "After the required confirmation, the strategy enters long at the next open.",
        "This is continuation after a pullback, not a VWAP fade. Direction comes from the existing trend.",
    ),
    "intraday_compression_breakout": _explanation(
        "Intraday compression breakout",
        "Find a narrow six-bar range after the open, freeze its boundaries, and trade the first confirmed expansion.",
        (
            ("Setup", "After 10:30, find the earliest rolling 30-minute range no wider than 0.50 or 0.75 of the initial opening range."),
            ("Entry", "Within the next 60 minutes, enter next open after the first completed close outside the frozen compression range."),
            ("Stop", "Use the opposite side of the frozen compression range."),
            ("Exit", "Test 1R and 1.5R targets; the daily forced flat remains 15:55."),
        ),
        (
            ("Compression fraction", "The narrow range's width divided by the initial opening-range width."),
            ("60-minute breakout window", "How long the frozen compression is eligible to break out."),
        ),
        "If the initial opening range is 100 points, a 0.50 candidate requires a later "
        "30-minute range no wider than 50 points before looking for a breakout.",
        "The 0.50 value measures relative range width. It does not mean the market moved 50%.",
    ),
    "opening_drive_continuation": STRATEGY_EXPLANATIONS["EXP-010"],
}

FAMILY_REPORT_HEADINGS: Mapping[str, str] = {
    "orb_pullback_continuation": "ORB pullback continuation",
    "failed_orb_reversal": "Failed ORB reversal",
    "vwap_mean_reversion": "VWAP mean reversion",
    "vwap_trend_pullback": "VWAP trend pullback",
    "intraday_compression_breakout": "Compression breakout",
    "opening_drive_continuation": "Opening drive continuation",
}


def _escape(value: str) -> str:
    return html.escape(str(value))


def explanation_html(
    explanation: StrategyExplanation,
    *,
    section_id: str = "strategy-rules",
    heading_level: int = 2,
    container_tag: str = "section",
) -> str:
    heading = max(1, min(int(heading_level), 6))
    tag = "div" if container_tag == "div" else "section"
    rule_cards = "".join(
        (
            '<div class="strategy-rule-card">'
            f"<h3>{_escape(label)}</h3><p>{_escape(text)}</p></div>"
        )
        for label, text in explanation.rules
    )
    parameter_rows = "".join(
        f"<tr><th>{_escape(label)}</th><td>{_escape(text)}</td></tr>"
        for label, text in explanation.parameters
    )
    return (
        f'<{tag} id="{_escape(section_id)}" '
        'class="strategy-explanation-section">'
        f"<h{heading}>How the strategy works</h{heading}>"
        f"<h3>{_escape(explanation.title)}</h3>"
        f'<p class="plain-language-lead">{_escape(explanation.idea)}</p>'
        f'<div class="strategy-rule-grid">{rule_cards}</div>'
        "<h3>What the parameters mean</h3>"
        '<table class="strategy-parameter-table"><tbody>'
        f"{parameter_rows}</tbody></table>"
        '<div class="strategy-example"><strong>Worked example</strong>'
        f"<p>{_escape(explanation.example)}</p></div>"
        '<div class="strategy-distinction"><strong>Important distinction</strong>'
        f"<p>{_escape(explanation.distinction)}</p></div>"
        f"</{tag}>"
    )


def strategy_explanation_html(
    experiment_id: str,
    *,
    section_id: str = "strategy-rules",
) -> str:
    key = str(experiment_id).upper()
    explanation = STRATEGY_EXPLANATIONS.get(key)
    if explanation is None:
        return (
            f'<section id="{_escape(section_id)}" '
            'class="strategy-explanation-section">'
            "<h2>How the strategy works</h2>"
            "<p>A plain-English strategy explanation has not yet been registered "
            f"for {_escape(key)}.</p></section>"
        )
    return explanation_html(explanation, section_id=section_id)


def family_explanation_html(
    family_id: str,
    *,
    section_id: str | None = None,
) -> str:
    explanation = FAMILY_EXPLANATIONS[str(family_id)]
    identifier = section_id or f"family-rules-{family_id}"
    return explanation_html(
        explanation,
        section_id=identifier,
        heading_level=3,
        container_tag="div",
    )
