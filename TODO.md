# TODO

- Bug (QT?): if a folder has another folder with the same name, both the folders are chosen even if the user choose only the first one (outer);
- Fix glitches (flickers) when widget rendering is too fast (some problem with minimum sizes?  ImageInfo different heights?);
- Fix not efficient check of selected widgets (now going through all);
- Render widgets while grouping them (now BlockedConnection is used, GUI freezes without it - too many signals per sec?);
- Get rid of 'multiprocessing' lib and use QT threads
