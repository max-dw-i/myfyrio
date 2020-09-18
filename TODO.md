# TODO

- Add a button for hiding the settings panel at the botton;
- Sign the cache and config files with hmac (https://stackoverflow.com/questions/24429307/hmac-signing-requests-in-python) or use, for example, json instead of pickle;
- Add 'Move', 'Delete' in the context menu;
- Embed the licenses into the application?;
- Add logo in 'About';
- Use QFormLayout in Preferences;
- Add new version check (and downloading, who knows...);
- Do not mark an image as chosen when click on it with the right mouse button;
- The FileDialog used already can select multiple folders using 'Ctrl', add the same feature for the 'pathsList';
- Bug (QT?): if a folder has another folder with the same name, both the folders are chosen even if the user choose only the first one (outer);
- Render widgets while grouping them (now BlockedConnection is used, GUI freezes without it - too many signals per sec?);
- Get rid of 'multiprocessing' lib and use QT threads;
- Replace bktree (at least, for large distances)?
