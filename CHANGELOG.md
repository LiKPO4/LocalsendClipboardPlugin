# Changelog

## 1.4.2

- Added a prominent update entry card to the main settings window.
- Added an immediate visible progress dialog while checking for updates.
- Added an HTML fallback when the GitHub Release API is rate limited.

## 1.4.1

- Improved the no-update feedback so users always get a clear completion dialog.
- Improved the self-update flow to prompt the user to close the running app before continuing installation.

## 1.3.0

- Reduced package size by removing extra notification dependencies and trimming the PyInstaller bundle.
- Improved clipboard copy reliability with retry logic and safer clipboard handle cleanup.
- Added Inno Setup based installer packaging for direct installation.
- Added repository metadata files for GitHub publishing, including `README.md` and `.gitignore`.

## 1.2.4

- Adjusted the notification implementation.
