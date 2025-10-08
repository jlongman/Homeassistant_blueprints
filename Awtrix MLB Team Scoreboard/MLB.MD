# Awtrix MLB Team Scoreboard

Adapting the Awtrix NFL Team Scoreboard to MLB.

## The Team Tracker API for MLB

From https://github.com/vasqued2/ha-teamtracker

Most of the same values from NFL and NHL are used but there are the following changes/additions:

The `quarter` shows the inning number but where we are in the inning is shown with the `clock` value.
The `clock` value will show for example, "Middle 7th" if we are in the middle of the 7th inning.   
```
clock 	The clock value within the quarter (should never be higher than 15:00). Inning (MLB only).
```

Additional properties for MLB which will be used to show the bases and outs. 
```
outs 	Number of outs (MLB only). 	IN
balls 	Number of balls (MLB only)). 	IN
strikes 	Number of strikes (MLB only). 	IN
on_first 	Baserunner on first base (MLB only). 	IN
on_second 	Baserunner on second base (MLB only). 	IN
on_third 	Baserunner on third base (MLB only). 	IN
```

## Display elements

### Background Color Distribution

**During Active At-Bat:**
- Team at bat occupies: pixels 0-20 (21 pixels)
- Other team occupies: pixels 22-31 (10 pixels)
- Divider: pixel 21 (black or contrasting color)

**Between Innings:**
- Occurs when: clock contains "Middle" or "End" of inning
- Home team: pixels 0-15 (16 pixels)
- Away team: pixels 16-31 (16 pixels)

### Secondary colour stripes

- Behind the scores are shown two vertical stripes of the secondary colour for each team.
- The stripes are 1 pixel wide and 8 pixels, separated by one pixel horizontally
- The stripes are shown in the middle of the left and right sections

### Bases Display (Middle Section, When Team is At Bat)
- Position: Centered horizontally in middle section (pixels 11-21), top portion
- Layout: Diamond formation with 3 pixels per base
    - Second base: pixel [14,1] (top of diamond)
    - First base: pixel [17,2] (right)
    - Third base: pixel [11,2] (left)
- Colors:
    - Loaded base: White (#FFFFFF)
    - Empty base: Grey (#5F5F5F)

### Outs Display
- Position: Below bases, centered in middle section
- 3 pips, each 1 pixel
- Horizontal spacing: 2 pixels between each pip
- Position: Row 5, pixels [13, 16, 19]
- Colors:
    - No out: Grey (#5F5F5F)
    - Out: White (#FFFFFF)

### Bottom Line Inning Display

**Pattern to use:** 9 innings centered with spaces, see Appendix
`xx_VH_VH_VH_VH_VH_VH_VH_VH_VH_xx`

**Pixel positions:**
- Start: pixel 3
- Each inning: 2 pixels (V and H)
- Space between innings: 1 pixel
- Positions: [3-4], [6-7], [9-10], [12-13], [15-16], [18-19], [21-22], [24-25], [27-28]

**Colors:**
- Visitor (V) pixel: Visitor team's primary color
- Home (H) pixel: Home team's primary color
- Current inning indicator: Brighten or add white border

**Extra innings (10+):**
- Compress spacing or shift left by 1 pixel
- Pattern: `_VH_VH_VH_VH_VH_VH_VH_VH_VH_VH_`

### Score Display in Side Sections

**Left Section (pixels 0-9):**
- Single digit: centered at pixel [4, 1]
- Double digit: starts at pixel [2, 1]
- Uses 3-pixel wide numbers + 1-pixel space

**Right Section (pixels 22-31):**
- Single digit: centered at pixel [26, 1]
- Double digit: starts at pixel [24, 1]


# Behaviour

This retains the pregame and postgame screens, showing when the game starts and the scores when done.
Innings are only shown when the game is in progress.


- During play
  - Relevant changes in the values of the API the different elements
  - The screen background shows the two team colours,
      - When one team is at bat their screen colour takes two thirds of the screen.
        - The home team is at bat when the clock has `Bottom` in it
        - The visitor team is at bat when the clock has `Top` in it
      - Between innings the screen colour is half half.
        - Between innings is indicated when `clock` has the string `Middle` in it
  - The horizontal left and right sections show the scores for each team
      - the background is the colour of the team
  - The horizontal middle section
      - when a team is at bat
          - has the background of the team at bat
          - at the top shows the bases which are loaded and unloaded
              - the bases are shown as a triangle of three boxes
          - underneath shows the outs as as pips
              - the pips grey if not, white if out
              - outs always proceed left to right
      - when no team is not at bat
          - the background is split in the middle
          - the number of the inning is shown cenetered horizonally
          - bottom of the inning there is a pip underneath the number of the inning
          - top of the inning there is a pip over the number of the inning
  - the bottom line across the entire screen shows the innings
      - as specified in the line with `9,  centered with spaces`
      - in extra innings we use `10,  centered with spaces`

### Trigger Events for Updates

1. **Inning change** (quarter attribute) → Update inning indicator and reset bases and outs
2. **Clock change** (clock attribute) → Update at-bat team background
3. **Bases change** (on_first, on_second, on_third) → Redraw bases
4. **Outs change** (outs attribute) → Update outs display
5. **Score change** (team_score, opponent_score) → Update scores + inning line      

### Game States

**PRE (Pregame):**
- Display: Game time and countdown
- Updates: Every minute

**IN (In Progress) - Between Innings:**
- Display: Current inning number with top/bottom indicator
- Background: Split 50/50

**IN (In Progress) - Active At-Bat:**
- Display: Bases, outs, scores
- Background: 2/3 for batting team

**POST (Postgame):**
- Display: Final scores
- Duration: [message_lifetime] hours    

### API Attribute to Display Element Mapping

| API Attribute | Display Element | Update Trigger |
|--------------|-----------------|----------------|
| team_score | Left/Right score | team_score change |
| opponent_score | Left/Right score | opponent_score change |
| quarter | Inning number, bottom line | quarter change |
| clock | At-bat indicator, background split | clock change |
| on_first | First base display | on_first change |
| on_second | Second base display | on_second change |
| on_third | Third base display | on_third change |
| outs | Outs pips | outs change |
| team_homeaway | Determines left/right placement | - |
| kickoff_in | Pregame countdown | kickoff_in change |

### Edge Cases

1. **Extra Innings (10+)**
    - How many extra innings to display? (10th only? 10-12?)
      - when we get to extra innings the 10th can stand in for all remaining innings
    - What if game goes to 15+ innings?

2. **Missing Data**
    - What if API returns null for bases/outs?
      - show the default state: empty bases, 0 outs
    - What if API returns null for team_score/opponent_score?
      - show the last known value or 0-0
    - What if API returns null for quarter/clock/on_first/on_second/on_third?
      - show the default state: 0-0, 0, 0, 0, 0
    - What if API returns null for outs?
      - show the default state: 0 outs
    - What if API returns null for team_homeaway?
      - show the default state: home team
    - What if API returns null for kickoff_in?
      - do not show the application

3. **Rapid Updates**
    - Debounce strategy if multiple attributes change simultaneously
    - Update order priority: scores > outs > bases

4. **Color Conflicts**
    - What if both teams have same primary color?
    - Fallback: use secondary colors or add border

5. **Suspended/Delayed Games**
    - How to display if game state changes from IN back to PRE?
    - Display "DELAYED" text?

6. **Playoffs/Special Games**
    - Any different display for postseason?

### Inning Number Display (Between Innings)

**When:** Clock contains "Middle" or "End"

**Display location:** Center of middle section (pixels 11-21)

**Rendering:**
- Single digit innings (1-9): Use Awtrix text at `{"dt":[14,2,"X",[255,255,255]]}`
- Double digit innings (10+): Use Awtrix text at `{"dt":[13,2,"XX",[255,255,255]]}`
- NO custom "1" needed here - standard text is fine for inning numbers

**Top/Bottom indicator pip:**
- Top of inning: White pixel at [15,1] (above inning number)
- Bottom of inning: White pixel at [15,4] (below inning number)
- Determination: "Top" in clock = top pip, "Bottom" in clock = bottom pip

### Horizontal Space Requirements

**Awtrix default font widths (approximate):**
- Most digits (0,2-9): ~4 pixels wide including 1-pixel spacing
- Digit "1" (text): ~2 pixels wide including spacing
- Custom "1": 2 pixels wide

**Score width examples:**
- "0" (single): 3 pixels
- "1" (custom): 2 pixels
- "05": 7 pixels (3 + 1 space + 3)
- "10": 6 pixels (2 custom + 4 text)
- "15": 6 pixels (2 custom + 4 text)
- "23": 8 pixels (4 + 1 space + 3)

This confirms scores fit comfortably in 10-pixel sections.

# Appendix

Information about the device and different patterns that could be used.

## The device

The Awtrix pixel dimensions are 8 high and 32 wide, 8x32

### Drawing Numbers

- A 1 can be done with 2 pixels wide and 5 pixels high
- Other Numbers can be 3 pixels wide, 5 pixels high.
- 10 and 12 through 19 can be represented as 6 pixels wide including the space between one and the next number
- 11 can be represented as 5 pixels wide including the space between one and the next one.
- Numbers start one pixel down from the top and end two from the bottom
- Numbers are drawn in white

#### Custom Number "1" for Scores

**When to use:**
- Only for scores containing "1" (01, 10-19, 21, 31, etc.)
- Replaces the Awtrix text "1" to save horizontal space

**Drawing specification:**
- Vertical line: 5 pixels tall (rows 1-5)
- Width: 2 pixels (one vertical line + one top pixel)
- Top pixel: positioned at [x, 1] (top-left of the vertical line)
- Vertical line: [x+1, 1] to [x+1, 5]
- Color: White (#FFFFFF)

**Example for "01" on left side:**

```javascript
[
    {"dp": [2, 1, "#FFFFFF"]},  // top pixel
    {"dl":[3,1,3,5,"#FFFFFF"]}, // vertical line 
    {"dt":[5,1,"0",[255,255,255]]} // use Awtrix text for "0"
]
```
**Example for "10" on left side:**
```javascript
[
    {"dp":[2,1,"#FFFFFF"]}, // top pixel 
    {"dl":[3,1,3,5,"#FFFFFF"]}, // vertical line 
    {"dt":[4,1,"0",[255,255,255]]} // use Awtrix text for "0"
]
```
### Score Display Using Awtrix Text Function

**Left Section (pixels 0-9):**
- Single digit without "1": Use `{"dt":[4,1,"X",[255,255,255]]}`
- Single digit "1": Custom draw at pixel [4,1]
- Double digit "00-09": Custom "0" at [2,1] + custom/text digit at [5,1]
- Double digit "10-19": Custom "1" at [2,1] + text digit at [4,1]
- Double digit "20-99": Text starting at `{"dt":[2,1,"XX",[255,255,255]]}`

**Right Section (pixels 22-31):**
- Single digit without "1": Use `{"dt":[26,1,"X",[255,255,255]]}`
- Single digit "1": Custom draw at pixel [26,1]
- Double digit "00-09": Custom "0" at [24,1] + custom/text digit at [27,1]
- Double digit "10-19": Custom "1" at [24,1] + text digit at [26,1]
- Double digit "20-99": Text starting at `{"dt":[24,1,"XX",[255,255,255]]}`

**Font to use:** Default Awtrix font (automatically sized)

### Score Rendering Logic

**Algorithm:**
1. Check if score contains "1" in tens or ones position
2. If tens digit is "1": Draw custom "1" + use text for ones digit
3. If ones digit is "1" and tens is "0": Draw custom "0" + custom "1"
4. Otherwise: Use Awtrix text function for entire score

**Template logic (pseudocode):**
```
if score == 1: 
    draw_custom_1(position) 
elif score >= 10 and score <= 19: 
    draw_custom_1(position) draw_text(ones_digit, position + 2) 
elif score % 10 == 1 and score < 10: 
    draw_text("0", position) draw_custom_1(position + 3) 
else: draw_text(score, position)
```


## The screen

```
1234567890 1234567890 1234567890 12
1234567890 1234567890 1234567890 12
1234567890 1234567890 1234567890 12
1234567890 1234567890 1234567890 12
1234567890 1234567890 1234567890 12
1234567890 1234567890 1234567890 12
1234567890 1234567890 1234567890 12
1234567890 1234567890 1234567890 12
```

## The screen divided in 3 sections, with 1 pixel between each section.

```
1234567890_1234567890_1234567890
1234567890_1234567890_1234567890
1234567890_1234567890_1234567890
1234567890_1234567890_1234567890
1234567890_1234567890_1234567890
1234567890_1234567890_1234567890
1234567890_1234567890_1234567890
1234567890_1234567890_1234567890 
```

## Masking numbers showing single digits

The top line is to position the numbers in the sections.
Single digits are aligned closer to the sides.

```
  XXX                       XXX 
1234567890_1234567890_1234567890 
1234567890_1234567890_1234567890 X
1234567890_1234567890_1234567890 X
1234567890_1234567890_1234567890 X
1234567890_1234567890_1234567890 X
1234567890_1234567890_1234567890 X
1234567890_1234567890_1234567890
1234567890_1234567890_1234567890 
```

## Masking numbers showing double digits

The top line is to position the numbers in the sections.
Double digits are laid out as follow.

```
 11 XXX                  11 XXX 
1234567890_1234567890_1234567890 
1234567890_1234567890_1234567890 X
1234567890_1234567890_1234567890 X
1234567890_1234567890_1234567890 X
1234567890_1234567890_1234567890 X
1234567890_1234567890_1234567890 X
1234567890_1234567890_1234567890
1234567890_1234567890_1234567890 
```

## The bottom line patterns for showing innings

This explores different ways of showing the innings.

```
1234567890_1234567890_1234567890 = template
123_567_901_345_789_123_567_901_ = 8,  uncentered, too small
12_45_78_01_34_67_90_23_56_89_12 = 11, centered
xx_45_78_01_34_67_90_23_56_89_xx = 9,  centered with spaces
.......112233445566778899....... = 9,  centered
```

### Extra innings

We explore how to show a 10th pip for extra innings.

```
1234567890_1234567890_1234567890 = template
123_567_901_345_789_123_567_901_ = 8,  uncentered, too small
12_45_78_01_34_67_90_23_56_89_12 = 11, centered
_45_78_01_34_67_90_23_56_89_XX_ = 10,  centered with spaces
......11223344556677889900...... = 10,  centered
```

### show home visitor patterns in innings

Different ways of showing the home and visitor patterns in the innings.  
The teams colours can be used to show which team is at bat.
V = visitor
H = home
number is placeholder

```
1234567890_1234567890_1234567890 = template
V2H_V6H_V0H_V4H_V8H_V2H_V6H_V0H_ = 8,  uncentered, too small
VH_VH_VH_VH_VH_VH_VH_VH_VH_VH_VH = 11, centered
xx_VH_VH_VH_VH_VH_VH_VH_VH_VH_xx = 9,  centered with spaces
.......VHVHVHVHVHVHVHVHVH....... = 9,  centered
```

### Awtrix Drawing Commands
Document the specific JSON commands used:
- `df` - Draw filled rectangle: {"df":[x, y, width, height, "color"]}
- `dp` - Draw pixel: {"dp":[x, y, "color"]}
- `dl` - Draw line: {"dl":[x1, y1, x2, y2, "color"]}
- `dt` - Draw text: {"dt":[x, y, "text", [r,g,b]]}
- `dr` - Draw rectangle (outline): {"dr":[x, y, width, height, "color"]}
