blender 5.0 插件
- 需要使用blender 5.0+ api
- 所有的function/operator/ui面板等，需要符合blender规范

## Release Packaging
- Local package: `python scripts/build_release_package.py`
- GitHub Release: push tag `vX.Y.Z`, or run `gh workflow run release.yml` to auto-bump patch version and release.
- Package script includes add-on root files, manifest, logo, README, and LICENSE; excludes workflow files, scripts, caches, and old zip outputs.
- Version source of truth: `blender_manifest.toml`.
- Workflow dispatch release bumps patch version automatically, commits `blender_manifest.toml`, tags `vX.Y.Z`, then builds/releases that exact tag.