# ERS Database Interface Boundary

This note captures the ERS-side contract for issue #70 without duplicating the storage backend that belongs in `bg-ers-iosubsystem`.

## Current ERS Boundary

ERS runtime code should continue to read and write assets only through `BG::ERS::IOSubsystem::IOSubsystem`.

Concrete ERS call sites already use this boundary:

- `SystemUtils->ERS_IOSubsystem_` owns the process-wide IOSubsystem instance.
- loaders call `ReadAsset(...)` for projects, scenes, shaders, models, scripts, controller settings, textures, and audio.
- writers call `WriteAsset(...)` for projects, scenes, scripts, models, textures, and controller settings.
- asset creation uses `AllocateAssetID(...)`.
- `Source/Main.cpp` passes local configuration and parsed CLI arguments into the IOSubsystem constructor.

The ERS process already exposes database-related configuration keys in `Config.yaml.in`:

- `UseDatabaseLoading`
- `DatabaseHost`
- `DatabasePort`
- `DatabaseUser`
- `DatabaseName`
- `DatabasePassword`

## Backend Ownership

The database connector implementation belongs in the external `bg-ers-iosubsystem` dependency because that package owns asset persistence and allocation semantics. ERS should not create a parallel Cassandra/PostgreSQL/filesystem storage path.

## ERS Acceptance Criteria

ERS-side work for a database backend is complete when:

1. The IOSubsystem package exposes a DB-backed implementation selected from configuration or CLI arguments.
2. ERS continues to call only `ReadAsset`, `WriteAsset`, and `AllocateAssetID`.
3. `UseDatabaseLoading` and `Database*` settings select the DB backend without changing loader/writer call sites.
4. The Cassandra sandbox in `Sandbox/Cassandra` can be used as an integration target for the IOSubsystem backend.
5. The ERS project/scene/model/shader/script load/save smoke path passes against both filesystem and DB-backed IOSubsystem modes.

## Non-Goals

- ERS should not implement database client code directly in renderer, loader, writer, or editor modules.
- ERS should not persist assets through ad hoc CQL, SQL, HTTP, or filesystem bypasses outside IOSubsystem.
- ERS should not make `UseDatabaseLoading` silently change behavior until IOSubsystem supports a concrete DB backend.
