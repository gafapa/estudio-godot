# Interactive audio implementation and verification

Use this guide when implementing sound feedback, ambience or music. Native Godot audio is a valid default; middleware is an optional project decision based on capabilities, licensing and deployment requirements.

## Event and mixing contract

Extend the style guide's feedback table or an assigned audio specification with:

| Field | Decision |
|---|---|
| Gameplay event | Actual signal/state transition and conditions for playback |
| Sound and variation | Asset family, variation/repetition policy and license |
| Routing | Bus, player volume control and priority relative to other sounds |
| Space | UI/non-spatial, 2D or 3D according to camera and gameplay |
| Lifetime | One-shot or loop; behavior on pause, exit, restart and scene change |
| Concurrency | Maximum simultaneous instances, priority and replacement policy |
| Accessibility | Visual/text alternative when the sound conveys necessary information |

React to gameplay contracts rather than development telemetry. Coordinate new signals with the Architect and their owners. Avoid hidden dependencies on asset paths throughout gameplay code.

## Budgets and transitions

Set provisional simultaneous-voice, memory and CPU limits for the target platform and expected peak load. Choose supported import formats and streaming/loading policies by asset length, repetition, latency and measurement; do not impose a universal duration cutoff.

When adaptive music serves the design, specify states or parameters, transition timing, fades and interruption behavior. Beat synchronization is useful when musically appropriate, not mandatory for every game. Verify repeated or rapidly changing states do not restart or stack tracks unintentionally.

## Verification

Exercise normal events, rapid repetition, peak concurrency, pause/resume, mute and volume persistence, scene changes and restart. Check for clipping, missing cues, excessive masking, abrupt loop boundaries and sounds that continue after their owner ends. Include spatial attenuation and occlusion only where the design uses them.

Record SHA, scenario, platform, audio configuration and measured resource usage where available. Listen to representative captures or real playback when tools permit. Event logs prove triggering, not audible quality; a headless or muted run cannot establish a successful listening check. Keep unavailable listening or target-device checks pending.

## Source

Workflow ideas adapted from [Agency Agents: Game Audio Engineer](https://github.com/msitarzewski/agency-agents/blob/main/game-development/game-audio-engineer.md). Middleware, spatialization and compression choices remain project-specific.
