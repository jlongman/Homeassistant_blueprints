# Next version

These are for version 2 and should not be implemented yet.

### Transitions

Transitions increase complexity and are not currently implemented.

**Score Change Animation:**
- Flash new score 3 times (100ms on/off)
- Or: No animation, instant update

**Inning Change:**
- Clear middle section
- Show inning number for 2 seconds
- Then return to bases/outs display

**Home Run / Big Play:**
- Optional: Flash entire screen in scoring team's colors


# Considerations


### 7. **Testing Scenarios**

#### Test Cases

1. **Pregame → Game Start**
   - Verify transition from countdown to active display
   - Check initial state: 0-0, top 1st, no runners, 0 outs

2. **Base Runner Scenarios**
   - Bases empty
   - Runner on first only
   - Bases loaded
   - All combinations (8 total states)

3. **Out Progression**
   - 0 outs → 1 out → 2 outs → 3 outs (inning change)
   - Verify pips update left to right

4. **Score Updates**
   - Single digit → double digit transition
   - Both teams scoring in same half-inning

5. **Inning Progression**
   - Top 1st → Middle 1st → Bottom 1st → End 1st → Top 2nd
   - Verify background split changes
   - Verify inning line updates

6. **Extra Innings**
   - Game reaching 10th, 11th, 12th+ innings
   - Verify bottom line adjusts correctly

7. **Home vs Away Display Mode**
   - Test with team as home team
   - Test with team as away team
   - Verify correct team on correct side per display_mode setting

8. **Postgame**
   - Final score display
   - Verify lifetime expiration after configured hours


### 8. **Configuration Options Documentation**

```markdown
### User Configuration Options

Beyond existing blueprint inputs, consider:

1. **Display Preferences**
   - Show/hide balls and strikes (currently not used)
   - Compact mode (no inning line on bottom)
   - Score-only mode (no bases/outs)

2. **Color Customization**
   - Override team colors
   - Custom "out" pip color
   - Custom "loaded base" color

3. **Update Frequency**
   - Throttle updates to prevent flashing
   - Minimum time between refreshes

4. **Animation Settings**
   - Enable/disable score change animations
   - Transition speed
```

### 9. **Implementation Algorithm Pseudocode**


### Core Update Logic

```pseudocode
function updateDisplay(gameState, attributes):
    if gameState == "PRE":
        return buildPregamePayload(attributes)
    
    else if gameState == "IN":
        if isBetweenInnings(attributes.clock):
            return buildBetweenInningsPayload(attributes)
        else:
            return buildActiveAtBatPayload(attributes)
    
    else if gameState == "POST":
        return buildPostgamePayload(attributes)

function buildActiveAtBatPayload(attrs):
    payload = initializePayload()
    
    // Determine which team is batting from clock
    battingTeam = getBattingTeam(attrs.clock)
    
    // Draw background split (2/3 for batting team)
    payload.addBackground(battingTeam, 2/3)
    
    // Draw scores
    payload.addScore("left", attrs.team_score)
    payload.addScore("right", attrs.opponent_score)
    
    // Draw bases
    payload.addBases(attrs.on_first, attrs.on_second, attrs.on_third)
    
    // Draw outs
    payload.addOuts(attrs.outs)
    
    // Draw inning line
    payload.addInningLine(attrs.quarter, attrs.team_score, attrs.opponent_score)
    
    return payload
```


### 10. **Dependency Matrix**

### Implementation Dependencies

**Must implement first:**
1. Color extraction from team attributes
2. Number rendering function (3x5 bitmap)
3. Background section splitter
4. Basic score display

**Can implement in parallel:**
- Bases display logic
- Outs display logic  
- Inning line display
- Game state handlers

**Implement last:**
- Animations/transitions
- Edge case handling
- Display mode switching


### 11. **Performance Considerations**

### Optimization Notes

1. **Payload Size**
   - Each MQTT payload should be < 4KB
   - Minimize redundant draw commands
   - Reuse color variables

2. **Update Frequency**
   - Don't update on every attribute change
   - Batch updates within 500ms window
   - Priority: score > outs > bases

3. **Display Duration**
   - Balance readability vs. responsiveness
   - Minimum 10 seconds during active play
   - Can reduce to 5 seconds during postgame



### Complete Payload Examples

**Example 1: Score is 3-1 (left team has 3, right team has 1)**
```json5
{ "draw": [], //..
, "duration": 15 }
```

**Example 2: Score is 10-12**
```json5
{
  "draw": [
    // ... backgrounds and stripes
    {"dp":[2,1,"#FFFFFF"]},
    {"dl":[3,1,3,5,"#FFFFFF"]},
    {"dt":[4,1,"0",[255,255,255]]},
    {"dp":[24,1,"#FFFFFF"]},
    {"dl":[25,1,25,5,"#FFFFFF"]},
    {"dt":[26,1,"2",[255,255,255]]},
    // ... bases, outs, inning line
  ],
  "duration": 15
}
```


### 7. **Implementation Priority**

### Build Order for Number Rendering

**Phase 1: Basic Text Rendering**
1. Implement Awtrix text-based scores for all cases
2. Test with scores 0-99
3. Verify positioning in left/right sections

**Phase 2: Custom "1" Integration**
1. Create function to detect "1" in scores
2. Implement custom "1" drawing
3. Create conditional logic to choose text vs custom
4. Test hybrid rendering with various score combinations

**Phase 3: Optimization**
1. Ensure alignment looks correct
2. Adjust positions if needed based on actual font rendering
3. Test edge cases (01, 10, 11, 21, etc.)


### 8. **Testing Matrix for Scores**

### Score Rendering Test Cases

| Score | Left Display | Right Display | Notes |
|-------|--------------|---------------|-------|
| 0-0 | Text "0" | Text "0" | Baseline |
| 1-0 | Custom "1" | Text "0" | Single custom |
| 0-1 | Text "0" | Custom "1" | Single custom |
| 10-5 | Custom "1" + Text "0" | Text "5" | Mixed left |
| 15-12 | Custom "1" + Text "5" | Custom "1" + Text "2" | Both mixed |
| 23-19 | Text "23" | Custom "1" + Text "9" | Mixed right |
| 11-11 | Custom "1" + Custom/Text "1" | Custom "1" + Custom/Text "1" | All ones |


This approach simplifies the implementation significantly because:

1. **Less custom drawing code** - Only need to handle "1" specially
2. **Awtrix handles font rendering** - No need to define pixel patterns for 0,2-9
3. **Automatic spacing** - Awtrix text function handles character spacing
4. **Clearer logic** - Simple conditional: "Does score contain 1? If yes, mix custom+text. If no, use text only."

The specification now needs clear rules for when to use custom vs text rendering, and
exact positioning for the hybrid approach.