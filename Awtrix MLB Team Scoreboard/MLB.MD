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

## The device

The Awtrix pixel dimensions are 8 high and 32 wide, 8x32

### Drawing Numbers

- A 1 can be done with 2 pixels wide and 5 pixels high
- Other Numbers can be 3 pixels wide, 5 pixels high.
- 10 and 12 through 19 can be represented as 6 pixels wide including the space between one and the next number
- 11 can be represented as 5 pixels wide including the space between one and the next one.
- Numbers start one pixel down from the top and end two from the bottom
- Numbers are drawn in white

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


## Behaviour

This retains the pregame and postgame screens, showing when the game starts and the scores when done.
Innings are only shown when the game is in progress.


- During play
  - Relevant changes in the values of the API the different elements
  - The screen background shows the two team colours,
      - When one team is at bat their screen colour takes two thirds of the screen.
      - Between innings the screen colour is half half.
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
      

    





