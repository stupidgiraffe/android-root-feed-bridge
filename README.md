# Android Root Feed Bridge

Automated, public, free module discovery feeds derived from [Best Root Apps for Android](https://github.com/krishna3163/best-root-apps-for-android).

This is an independent index. It never packages APKs, LSPosed applications, or arbitrary ZIPs as root modules. Release ZIPs must contain a valid `module.prop` at ZIP root. Binaries are hosted by the original developers, not mirrored.

## Add to your apps

**MMRL** → Repositories → Add (paste base URL):

```text
https://raw.githubusercontent.com/stupidgiraffe/android-root-feed-bridge/main/
```

**KernelSU Next** → Module repository → Manage repositories → Add (paste full JSON URL):

```text
https://raw.githubusercontent.com/stupidgiraffe/android-root-feed-bridge/main/ksu/modules.json
```

**Whole catalog (apps, LSPosed, tools, and modules):** [discovery.json](discovery.json)

## How it updates

The [GitHub Actions workflow](.github/workflows/update.yml) runs daily at approximately 18:17 JST and can also be manually triggered. It reads the upstream catalog and 60 configured release trackers; checks newly discovered projects in batches; fetches the latest GitHub release for each candidate; downloads and inspects ZIPs without executing them; and writes two different JSON index formats.

MMRL lists the validated release's version and exact ZIP. KernelSU Next lists the GitHub project **only if its latest release has exactly one ZIP**, because its manager selects the first release ZIP without inspecting archive contents. Non-installable discoveries go in `discovery.json`, not either install feed.

If an upstream fetch fails or output contains no verified modules, generation stops without publishing an empty or misleading feed. Unit tests and structural validation run before each commit. Generated data goes in `json/modules.json`, `ksu/modules.json`, `state.json`, and `discovery.json`.

GitHub Actions on public repositories is free under ordinary usage. GitHub can delay scheduled workflows or automatically disable them after extended repository inactivity. This is low-maintenance rather than a guarantee of perpetual operation.

**Security:** An inspectable ZIP and valid `module.prop` prove packaging, **not module safety or device compatibility**. Check each project before flashing. Modules may need permanent root, reboot, a matching kernel, or Zygisk. Original authors retain their licenses and ownership.
