# Native Tree Tabs on Fedora Kinoite

How to run `NativeTreeTabs.uc.js` with Fedora's own Firefox (the `firefox` RPM
in the base image) on Fedora Kinoite / other rpm-ostree desktops.

## Why this needs extra steps

Firefox can't load `.uc.js` scripts by itself. It needs a loader such as
[fx-autoconfig](https://github.com/GAlexandruD/fx-autoconfig) (a fork of
[MrOtherGuy/fx-autoconfig](https://github.com/MrOtherGuy/fx-autoconfig)).
The loader has two parts:

| Part | Where it goes | How it's installed here |
|---|---|---|
| Program files: `config.js`, `defaults/pref/config-prefs.js` | Firefox's install folder, `/usr/lib64/firefox` | A small RPM layered with `rpm-ostree`, since `/usr` is read-only on Kinoite |
| Profile files: `chrome/utils/*` | Each Firefox profile | Copied from the fx-autoconfig repo |

The loader only does something in profiles that contain
`chrome/utils/chrome.manifest`. Profiles you don't set up behave exactly as
before.

## What's in this repo

```
kinoite/rpm/
├── SPECS/firefox-fx-autoconfig.spec      # spec file for the loader RPM
├── SOURCES/                              # config.js, config-prefs.js, LICENSE
│                                         #   (from fx-autoconfig commit dfdab56)
└── RPMS/x86_64/firefox-fx-autoconfig-0-1.gitdfdab56.fc44.x86_64.rpm
```

The RPM installs only these three files. It depends on `firefox` and has no
install scripts:

```
/usr/lib64/firefox/config.js
/usr/lib64/firefox/defaults/pref/config-prefs.js
/usr/share/licenses/firefox-fx-autoconfig/LICENSE
```

## Install

The examples assume both repos are cloned in `~/Documents/repos`:

```bash
cd ~/Documents/repos
git clone https://github.com/GAlexandruD/NativeTreeTabs.git
git clone https://github.com/GAlexandruD/fx-autoconfig.git
```

### 1. Layer the loader RPM (once per machine)

```bash
sudo rpm-ostree install --apply-live \
  ~/Documents/repos/NativeTreeTabs/kinoite/rpm/RPMS/x86_64/firefox-fx-autoconfig-0-1.gitdfdab56.fc44.x86_64.rpm
```

`--apply-live` makes the files available right away, without a reboot. The
package stays layered across OS updates. Check that it's installed:

```bash
rpm-ostree status          # listed under "LocalPackages"
rpm -V firefox-fx-autoconfig   # no output, or only "T" (timestamp) flags = OK
```

### 2. Set up each profile

Find the profile folder in `about:profiles` ("Root Directory"). On this
machine, profiles are in `~/.config/mozilla/firefox/`. Run this once for each
profile:

```bash
PROFILE=~/.config/mozilla/firefox/xxxxxxxx.default-release   # change this
REPOS=~/Documents/repos

# fx-autoconfig profile files
mkdir -p "$PROFILE/chrome/utils" "$PROFILE/chrome/JS" "$PROFILE/chrome/CSS" "$PROFILE/chrome/resources"
cp "$REPOS"/fx-autoconfig/profile/chrome/utils/* "$PROFILE/chrome/utils/"

# The script: a symlink, so edits in this repo apply to every profile
ln -sfn "$REPOS/NativeTreeTabs/NativeTreeTabs.uc.js" "$PROFILE/chrome/JS/NativeTreeTabs.uc.js"

# Keep the script's self-updater off. user.js is re-applied at every startup.
cat >> "$PROFILE/user.js" <<'EOF'
// Native Tree Tabs: keep the script's self-updater off
user_pref("treeTabs.update.autoUpdate", false);
user_pref("treeTabs.update.insiderVersions", false);
EOF
```

If the profile already has a `user.js`, the `>>` adds these lines to the end of
it. Run the `cat` command only once per profile.

### 3. Restart Firefox

Close **every** Firefox window of that profile (the loader is only read at
startup) and start it again. Tree tabs should appear in the vertical tab strip.

If they don't, open `about:support`, click **Clear startup cache…**, and let
Firefox restart. Errors show up in the Browser Console (`Ctrl+Shift+J`).

## Why auto-update is off

By default, the script checks GitHub 1.5 s after startup and then every
20 minutes. When there's a newer version, it overwrites its own file, and the
new code runs with full browser privileges at the next restart.

- The stable channel checks a PGP signature against a key built into the
  script.
- The "insider versions" channel skips that check.

The `user.js` lines above turn both off. Updates then only happen when you
pull and review them in git.

Note: the script's `REPO` constant (line 29 of `NativeTreeTabs.uc.js`) still
points to `ATechnocratis/NativeTreeTabs`. The **Update** button in the
script's settings downloads from there, not from this fork.

## Updating

**The script:** pull, or edit, in this repo and restart Firefox. Every
profile uses the symlink, so they all pick up the change.

```bash
cd ~/Documents/repos/NativeTreeTabs
git remote add upstream https://github.com/ATechnocratis/NativeTreeTabs.git   # once
git fetch upstream
git log -p HEAD..upstream/main -- NativeTreeTabs.uc.js   # review first
git merge upstream/main
```

**fx-autoconfig profile files** (`chrome/utils`): after pulling the
fx-autoconfig repo, copy `profile/chrome/utils/*` into each profile again and
restart Firefox.

**fx-autoconfig program files:** these almost never change. If
`program/config.js` or `program/defaults/pref/config-prefs.js` change
upstream, rebuild the RPM (below) and replace the layered package.

## Rebuilding the RPM

`rpmbuild` isn't on the Kinoite host, so this builds inside a throwaway
Fedora container:

```bash
cd ~/Documents/repos/NativeTreeTabs/kinoite/rpm
# refresh sources from fx-autoconfig if needed:
cp ../../../fx-autoconfig/program/config.js ../../../fx-autoconfig/program/defaults/pref/config-prefs.js \
   ../../../fx-autoconfig/LICENSE SOURCES/
# bump Release: in SPECS/firefox-fx-autoconfig.spec, then:
podman run --rm -v "$PWD":/build:Z registry.fedoraproject.org/fedora:44 bash -c \
  'dnf -q -y install rpm-build && rpmbuild --define "_topdir /build" -bb /build/SPECS/firefox-fx-autoconfig.spec'
```

Swap the layered package for the new one in a single transaction:

```bash
sudo rpm-ostree uninstall firefox-fx-autoconfig \
  --install ./RPMS/x86_64/firefox-fx-autoconfig-<new-version>.rpm
systemctl reboot
```

## Uninstall

```bash
sudo rpm-ostree uninstall firefox-fx-autoconfig
systemctl reboot
```

Then, in each profile:

- delete `chrome/utils/` and `chrome/JS/NativeTreeTabs.uc.js`
- remove the Native Tree Tabs lines from `user.js`

The script also changed a few Firefox settings, which you may want to reset in
`about:config`:

- `sidebar.verticalTabs = true`
- `sidebar.visibility = always-show`
- `browser.tabs.dragDrop.createGroup.enabled = false`
- `browser.tabs.groups.smart.enabled = false`
- `svg.context-properties.content.enabled = true`
