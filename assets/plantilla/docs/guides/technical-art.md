# Technical art budgets and asset validation

Use this guide when producing or integrating visual assets, shaders or effects. Select only the checks relevant to the game's dimension, renderer and target platforms.

## Establish a measurable budget

Before a representative art batch, the technical artist and platform engineer agree on provisional limits in `docs/arte/guia_estilo.md`. Include target hardware, renderer, resolution, frame-time target, representative scene and worst expected asset density. Mark unmeasured limits as hypotheses.

Track the constraints that could affect this game: texture memory and dimensions, visible geometry, material/draw-call count, simultaneous particles, transparency/overdraw, animation cost and loading time. Record shared frame budgets once; subsystem budgets must fit within them. Do not adopt example triangle counts, compression formats or fixed LOD counts without checking platform support and need.

## Import and handoff

For each asset family, specify source format, scale, pivot/origin, naming, collision expectations, material slots and relevant animation conventions. Verify in Godot under production lighting, camera distance and intended resolutions.

- Check texture filtering, compression and mipmaps for the actual use: pixel art, UI and world textures can need different settings.
- Check seams, transparency, silhouette, collision and animation transitions where applicable.
- Add LOD, atlasing or instancing only when measurements or expected scale justify them; check visual transitions and batching assumptions in-engine.
- Give exposed shader parameters meaningful ranges and descriptions. Confirm syntax and feature support against the installed Godot version and chosen renderer.
- Record source and license through an assigned update to `assets/LICENSES.md`.

## Profile representative load

Use the actual gameplay camera and maximum expected concurrent assets/effects. Record SHA, scene, hardware, renderer, resolution, settings, sample duration and profiler evidence. Separate CPU and GPU costs where tools expose them; report frame-time spikes as well as typical performance. Keep screenshot evidence for readability and appearance.

Compare before/after measurements for optimizations. Recheck visual quality after changing imports, LOD or shaders. A headless run or static image cannot establish GPU performance; testing on one machine does not qualify other target hardware.

When a feature exceeds budget, propose a measured quality reduction, density limit or optional fallback. Preserve the game's visual intent and record tradeoffs with the Producer rather than silently lowering quality.

## Source

Workflow ideas adapted from [Agency Agents: Technical Artist](https://github.com/msitarzewski/agency-agents/blob/main/game-development/technical-artist.md). Its engine-specific examples and fixed budgets are not Godot requirements.
