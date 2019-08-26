![GUI screenshot](https://raw.githubusercontent.com/oratosquilla-oratoria/doppelganger/master/docs/resources/gui.png)

## Doppelgänger

Doppelgänger is a program that searches for similar images. To find them, perceptual hashes are used, in particular, so-called [Difference hash](https://www.hackerfactor.com/blog/index.php?/archives/529-Kind-of-Like-That.html). Two images are the same if they have equal hashes and, therefore, are marked as duplicates.

It works great when you want to find exact (or almost, for example, slightly altered lighting, cropping) duplicates. Although sometimes we can get **false positives** (the hashes are the same but the images are different) and sometimes - **false negatives** (the images are quite similar, but the hashes are very different). Nevertheless these are rather rare.

## Main features

- Caching

The calculated hash of an image is kept in the cache file. If you need to do a new search, the program takes the already known hashes from the cache and calculates only the unknown ones.

- Parallel calculating

If you have a multi-core processor, the program utilizes all the cores.

- Sensitivity levels

There are 3 sensitivity levels: high, middle, low. If you choose the high level, you will get the most similar images. The lower level is, the more chances are to get false positives.

- GUI

User friendly interface. For example, you get big thumbnails so you can see the difference between the images immediately; similar images are grouped and are not shown in pairs (as in the majority of programs with similar functions); you cannot press a button if it cannot be used now; under every image there is information about its resolution, file size and path, etc.

- Moving or deletion of the selected images

You can delete the selected images or move them into another folder.

- Supported formats

The program can process BMP, JPG, PNG (yet).

## Installation

This program requires Python 3.7 or higher and a few modules. To install:

```bash

# Clone the repository
git clone git@github.com:oratosquilla-oratoria/doppelganger.git
# Install the necessary dependencies
pip install -r requirements.txt
# Run the program
python3 main.py

```

## Usage

![GUI gif](https://raw.githubusercontent.com/oratosquilla-oratoria/doppelganger/master/docs/resources/gui.gif)

First of all, you have to add the folders you want to search for similar images in. To do that, press button **Add Folder** and add as many folders as you need. If you have added some folder by mistake, choose it and press button **Remove Folder**. Then choose a sensitivity level and press button **Start**. Wait for some time and get the result. If you need to stop the process, press button **Stop**.

Check the found 'duplicates', select those that you want to delete or move into another folder, and press the necessary button (**Delete** or **Move**). In the latter case, you will also have to choose a new folder for the selected images. That is it.

## Tests

The program is partly covered by unit tests. To run them:

```bash

python3 -m unittest

```
