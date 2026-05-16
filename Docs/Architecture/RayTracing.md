# Ray Tracing Architecture Boundary

This note captures the first implementation boundary for issue #86. The current renderer is an OpenGL raster pipeline, so a useful ray tracing implementation needs an explicit backend and data-path decision before adding UI toggles or settings.

## Current Renderer State

The current runtime path is centered on:

- `RendererManager` for renderer startup and window/context ownership.
- `VisualRenderer` for viewport orchestration, shader updates, editor/play mode transitions, and scene drawing.
- `MeshRenderer` and `DrawMesh` for raster mesh submission.
- GLSL shader programs for vertex, fragment, geometry, compute, tessellation-control, and tessellation-evaluation stages.

There is no current acceleration-structure builder, ray-generation/miss/hit shader stage model, ray traced output target, material export path, Vulkan/OptiX/DXR backend, or CPU reference tracer.

## Required Backend Decision

Pick one first backend before implementation:

- Vulkan ray tracing for production GPU acceleration.
- OptiX for NVIDIA-only experimentation.
- CPU reference tracer for correctness-first validation.
- OpenGL compute fallback for portability at lower performance.

The first backend should define:

1. how ERS models, meshes, materials, lights, cameras, and textures are exported into ray-tracing scene data;
2. how acceleration structures or CPU spatial indexes are built and invalidated;
3. how the ray traced image is written into an ERS viewport or offscreen render target;
4. how raster and ray traced modes share camera, project, and renderer settings;
5. how the feature is tested with one deterministic scene.

## First Slice

The smallest useful first slice is a non-UI backend spike that renders a deterministic ray traced image from a tiny scene and verifies the output path. A settings toggle should come after a backend can actually render.

## Non-Goals

- Do not add `RayTracingEnabled` UI/config flags without a backend.
- Do not mix ray tracing storage or material conversion into unrelated renderer settings patches.
- Do not require the full editor to run before a headless/backend validation target exists.
