# TODO

- Icon (low resolution - https://doc.qt.io/qt-5/appicon.html);
- Use QFormLayout in Preferences;
- Do not mark an image as chosen when click on it with the right mouse button;
- The FileDialog used already can select multiple folders using 'Ctrl', add the same feature for the 'pathsList';
- Bug (QT?): if a folder has another folder with the same name, both the folders are chosen even if the user choose only the first one (outer);
- Render widgets while grouping them (now BlockedConnection is used, GUI freezes without it - too many signals per sec?);
- Get rid of 'multiprocessing' lib and use QT threads
