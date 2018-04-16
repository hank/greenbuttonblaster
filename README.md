# Green Button Blaster

Script to push the Green Button at Baltimore Gas and Electric's website
periodically to download the latest data. This is nice for applications
such as

## Requirements

* Python 3.6+
* Firefox
* geckodriver 0.20.1 in your PATH

## Instructions

* Install python requirements with `pip -r requirements.txt`
* Put your settings in `settings.txt`
* Run the script

## Inner Workings

This script works by authenticating with BG&E, going to the Green Button
export URL, and requesting a CSV of a range of days. The zip is downloaded,
opened and processed with Python's CSV library. This export then occurs once
per hour.
