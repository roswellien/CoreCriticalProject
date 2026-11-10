# The AI arena (ours, #287)

A test tool, not part of play: AI bots fight each other in a multiplayer match
on one computer, so changes to the AI can be measured. Nothing here runs in the
campaign, Instant Action or a normal multiplayer game.

## The hunt order (`mech3/zai_hunt`)

Stock MW3 moves its AI along route nets the designers laid by hand for each
campaign mission (ai.md sections 8 to 10). Multiplayer maps ship none, so a bot
placed there would have nowhere to go. The hunt order gives it a goal:

1. the nearest enemy its sensors have a contact on;
2. else the place where it last saw an enemy, until it comes within 30 m;
3. else a fallback point the arena sets for the whole map (the middle of the
   map's spawn spots), where it stands and waits.

It walks there by the walkability grid (`zai_nav`, lancemate-pathing.md) when
the straight way is blocked, and straight otherwise. The grid is behind bug
fixes, as the lancemates' is; the arena refuses `--original`.

The hunt doesn't fight. Its net allows an attack, so once an enemy is within
the pilot's attack range the stock engage gate (ai.md 17.3) pushes the stock
fight on top, with the stock targeting, firing and weapon choice. When that
fight ends the hunt runs again.

All bots share one hunt net, as the game's lancemates share one formation net;
each bot's goal, last-seen place and grid way live in its own order.

## Setup and match log

Added with the arena run (#287, second PR).
