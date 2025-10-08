# Implementation Plan: Awtrix MLB Team Scoreboard
Incremental steps that are easy to test directly from the current MLB template. We start with plain text rendering for all scores (including double digits) and migrate to the custom “1” design at the end.

Goals:
- Keep every phase independently testable.
- Avoid breaking existing behavior during iterations.
- Use Awtrix text for all scores first; only in the final steps switch to custom “1” to optimize spacing.

---

## Phase 1: Foundation — MLB Attributes and Inning State

Step 1.1: Add MLB attribute variables
- Add variables for: current_inning, inning_state, outs_count, on_first, on_second, on_third.
- Use defaults for missing data (e.g., outs 0, runners false).

Test:
- Reload the automation/template.
- Verify no template errors in logs.
- Use Developer Tools → Template to render the new variables (sanity check).

Step 1.2: Add inning state helpers
- Add booleans: is_top_inning (“Top” in clock), is_bottom_inning (“Bottom” in clock), is_middle_inning (“Middle” or “End” in clock).

Test:
- Mock the clock attribute to “Top 1st”, “Middle 1st”, “Bottom 1st”.
- Verify the booleans evaluate as expected in Developer Tools → Template.

---

## Phase 2: Scores — Simple Text Rendering Everywhere

Step 2.1: Simplify score variables
- Ensure left_team_score and right_team_score return plain score strings (no zero-padding).
- Keep the use of the default Awtrix text function for both sides.

Step 2.2: Position scores using text (no custom digits)
- Left text at [4,1].
- Right text at [26,1].
- This works for single- and double-digit scores (10–99) using the default font.

Test:
- Set scores to: 0–0, 5–3, 10–15, 21–19.
- Confirm readability and alignment visually.

Rollback Strategy:
- Keep originals commented if needed for quick revert.

---

## Phase 3: Middle Section — Bases Display

Step 3.1: Add bases_display variable
- Use three pixels in a diamond:
  - Second base at [14,1]
  - First base at [17,2]
  - Third base at [11,2]
- Color white when occupied, grey when empty.
- Draw only during active at-bat (not during “Middle”/“End”).

Test:
- Manually toggle on_first/on_second/on_third.
- Verify pixels update accordingly (empty vs occupied).
- Confirm nothing is drawn when is_middle_inning.

---

## Phase 4: Middle Section — Outs Display

Step 4.1: Add outs_display variable
- Three pips on row 5 at [13,5], [16,5], [19,5].
- Grey for not out, white for out.
- Draw only during active at-bat (not during “Middle”/“End”).

Test:
- Set outs 0 → 1 → 2 → 3.
- Confirm pips turn white left to right.
- Confirm they do not show during “Middle”/“End”.

---

## Phase 5: Between-Innings Inning Number

Step 5.1: Add inning_display variable
- Between innings (is_middle_inning): 
  - Show inning number centered in the middle section.
  - Single-digit use text at [14,2]; double-digit at [13,2].
  - Add a pip: top at [15,1] if “Top” in clock; bottom at [15,4] if “Bottom”.

Test:
- Clock = “Middle 5th” → show “5” centered with no bases/outs.
- Clock = “End of 1st” (if used) → treat as between innings.

---

## Phase 6: MLB-Specific Payloads

Step 6.1: Build active at-bat payload
- Background split:
  - Top inning: left team occupies ~2/3 (0–20 or 0–21), right the rest (22–31).
  - Bottom inning: right team occupies ~2/3 (11–31), left the rest (0–10).
- Add two vertical secondary color stripes in each side section.
- Draw scores via text at [4,1] and [26,1].
- Draw bases_display and outs_display.

Test:
- Simulate Top/Bottom inning transitions via clock attribute.
- Verify background split and that bases/outs appear only in active at-bat.

Step 6.2: Build between-innings payload
- 50/50 background split (0–15, 16–31).
- Keep score text at [4,1] and [26,1].
- Draw inning_display only (no bases/outs).

Test:
- Set clock to “Middle Xth”, verify inning number/pip and no bases/outs.

---

## Phase 7: MLB Triggers

Step 7.1: Add triggers for MLB updates
- Add state triggers for attributes: clock, outs, on_first, on_second, on_third.
- Keep existing score and inning triggers.

Test:
- Change each attribute in Developer Tools and confirm automations fire (using traces).

---

## Phase 8: Action Logic — Route to MLB Payloads

Step 8.1: Replace/augment routing logic
- If game state is IN and is_middle_inning → publish between-innings payload.
- If game state is IN and not is_middle_inning → publish active at-bat payload.
- Score changes should route to the current view (active vs between).
- Maintain pregame and postgame flows as they are.

Test:
- Full flow: PRE → IN (Top) → Middle → IN (Bottom) → POST.
- Verify correct payload switches at each stage.

---

## Phase 9: Inning Line (Bottom Row)

Step 9.1: Create inning_line variable
- 9 innings centered with spaces using positions:
  - Start at x=3 for 9 innings; for 10th+ use x=2 to fit.
  - For each inning i: draw two pixels (visitor then home) in team colors.
  - Highlight the current inning by drawing both pixels in white.

Step 9.2: Add inning_line to MLB payloads
- Append inning_line to both active and between-innings payloads.

Test:
- Verify 9 pips across the bottom.
- Current inning highlighted white.
- At 10th inning, show 10 pips (compressed start position).

---

## Phase 10: Migration to Custom “1” (Optional Final Optimization)

Step 10.1: Prepare score value helpers
- Add integer score helpers for left/right to simplify logic.

Step 10.2: Implement left_score_draw (custom “1”)
- If score == 1: draw top-left pixel plus vertical line (“2 px wide, 5 px tall”).
- If 10–19: draw custom “1” + Awtrix text for ones digit.
- If single digit (not 1): draw text centered at [4,1].
- If 20–99: draw full text starting at [2,1].

Step 10.3: Implement right_score_draw (custom “1”)
- Mirror left logic:
  - Custom “1” is drawn starting at [26,1] with vertical line at x=27.
  - For 10–19: custom “1” at [24..25] plus ones digit at [26,1], etc.

Step 10.4: Switch payloads to use custom draws
- Replace direct text draws with left_score_draw and right_score_draw.

Step 10.5: Add a feature flag (optional)
- Add a toggle to enable/disable custom “1”.
- Default off to keep behavior predictable; turn on after validation.

Tests for Migration:
- Score matrix visual checks:
  - 0–0 → Text “0 / 0”
  - 1–0 → Custom “1” / Text “0”
  - 10–5 → Custom “1” + “0” / “5”
  - 15–12 → Custom “1” + “5” / Custom “1” + “2”
  - 21–19 → “21” (text) / Custom “1” + “9”
- Verify spacing, alignment, and legibility in both sections.

Rollback Strategy:
- Keep the original plain-text score lines available to revert quickly if needed.

---

## Final QA and Observability

Checklist:
- No template errors on reload.
- All triggers fire and route to the correct payloads.
- Scores, bases, outs, inning number, and inning line update in real time.
- Extra innings display correctly (10th pip appears).
- Postgame lifetime honored.

Optional Enhancements (Future):
- Debug mode: log selected attributes for troubleshooting.
- Throttling updates (batch within 500 ms) if needed.
- Config options to hide inning line or switch to score-only mode.

Tools for Testing:
- Developer Tools → Template (evaluate variables).
- Automation trace (ensure correct branches execute).
- Visual device checks during live or simulated game data.

This plan ensures the MLB scoreboard becomes fully functional with clear, testable milestones. The custom “1” rollout is isolated to the final phase to keep early milestones simple and reliable.
