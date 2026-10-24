# Level design and spatial playtesting

Use this guide when player movement, rooms, encounters or generated maps carry meaningful decisions. For abstract or menu-driven games, skip spatial deliverables that do not apply.

## Design before decoration

The game designer specifies the intended experience in an assigned `docs/design/levels/` document. The Producer assigns implementation paths to the technical artist or gameplay engineer; content ownership alone does not authorize scene or code changes.

For a representative level or reusable room family, record:

- Player goal, entry state, available verbs and exit or failure conditions.
- A small path graph showing required objectives, optional rewards, gates and recovery routes.
- Expected pacing beats, where the player learns a mechanic, and where it is tested.
- Navigation cues using geometry, landmarks, contrast or sound, with alternatives when color or hearing is unavailable.
- Relevant encounter constraints: warning time, sight lines, tactical choices and safe recovery. Omit combat assumptions for games without combat.
- Gameplay-critical geometry and collision that an art pass must preserve.

Build a small playable blockout using simple geometry or tiles. Test readability, traversal and the intended decisions before investing in detailed decoration. Treat layout approval as a working baseline; later evidence can justify changes.

## Evidence and iteration

Choose thresholds from the game's movement speed, camera, audience and intended challenge. Do not impose universal room dimensions, navigation times or numbers of tactical routes.

Record the build SHA, level ID, initial state, input method and seed where relevant. Compare intended and observed route, completion time, missed cues, retries and recovery. Capture before/after views from the actual game camera when changing layout.

Bots can test reachability and timing; fresh human observation is needed to assess whether cues are understandable without assistance. Record unavailable human testing as pending. Recheck navigation and collision after the art pass.

For procedural layouts, test a reproducible seed sample and relevant invariants: reachable objectives, valid entrances/exits, key-before-lock ordering, spawn safety and a completion route. Retain failing seeds as regression cases; sampled success does not prove all seeds valid.

## Source

Workflow ideas adapted from [Agency Agents: Level Designer](https://github.com/msitarzewski/agency-agents/blob/main/game-development/level-designer.md). Apply project-specific criteria rather than its universal rules or example thresholds.
