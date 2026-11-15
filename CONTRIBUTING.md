# Contributing to RootAtlas

RootAtlas is an independent module **index**, not a binary hosting service.
New sources, bug fixes and responsible metadata improvements are welcome.

## Propose a repository

Open an issue with the feed's public HTTPS URL and the original publisher's
GitHub project. For MMRL, it must serve `json/modules.json` in the
MMRL schema. For KernelSU Next, it must serve a top-level `modules.json`
array of GitHub repositories with valid names, authors and descriptions.
A repository should be actively maintained and have real, installable
module releases. Do not submit mirrors of the RootAtlas feed itself.

Automatic GitHub discovery is best-effort and will not find every third-party
host or privately distributed source. See
[`sources/federation.json`](sources/federation.json) for curated additions.

## Integrity and source policy

- Links are original developer-hosted resources; never submit modified,
  repacked or unauthorized APKs/ZIPs.
- A valid `module.prop` or JSON format does **not** make a module safe.
- The maintainer may reject stale, cloned, misleading or dangerous sources.
- Independent discovered feeds may **add** IDs, but cannot replace modules
  already supplied by established sources.
- Do not advertise root-hiding, bypass, compatibility or security as tested
  unless directly supported by reproducible evidence.
- Keep LSPosed/Xposed APK projects out of MMRL and KernelSU Next flashable
  ZIP feeds. See [the architecture](docs/ARCHITECTURE.md).

## Development

Test with `python -m unittest discover -s tests -v`. The GitHub Actions job
renders the banner, refreshes sources, validates all manager contracts, and
publishes generated JSON only on success.

Changes to generated JSON alone will be overwritten on the next run.
Update the source parser, discovery rules or curated source configuration.

No Android device is required to contribute; RootAtlas does not install
modules or run a phone-resident daemon.

## Credits and license

The indexer source code is [MIT licensed](LICENSE). Every original module,
catalog, feed and referenced binary retains its **own** publisher,
copyright and license. RootAtlas does not grant permission to rehost them.
