# Scolendar API
[![Build Status](https://travis-ci.com/tag166tt/l3_s6_projet_bdd_api.svg?token=hfWoGD6NjtKs6Vbqwnfs&branch=master)](https://travis-ci.com/tag166tt/l3_s6_projet_bdd_api)
![Django CI Ubuntu](https://github.com/tag166tt/l3_s6_projet_bdd_api/workflows/Django%20CI%20Ubuntu/badge.svg?branch=master)
![Django CI Windows](https://github.com/tag166tt/l3_s6_projet_bdd_api/workflows/Django%20CI%20Windows/badge.svg?branch=master)
![Django CI MacOS](https://github.com/tag166tt/l3_s6_projet_bdd_api/workflows/Django%20CI%20MacOS/badge.svg?branch=master)
[![Dependabot](https://badgen.net/badge/Dependabot/enabled/green?icon=dependabot)](https://dependabot.com/)

## Supported platforms
Code is automatically tested on latest versions Windows, Ubuntu and MacOS available in Github Actions.

The project also contains necessary files to run as a container. The container build is also tested in Github Actions.

Project is tested with the following Python versions:
- 3.6
- 3.7
- 3.8

## How to start the server?
### Run locally
Build scripts are included in the project to run DB migrations and setup a basic super user. You first need to create a python virtual environment for the scripts to work.
The folder containing the virtual environment should be named:
- `venv` on Windows
- `.venv` on Linux

Let PyCharm create it on Windows, and if you're on Linux, you should know how to do this anyway 😊

The scripts should be run before starting the app. Thee following guide will show you how to add the proper script to run before build.

### Run in a container
The project can be run in a container.
You need to build it and then run it as usual.

## Use the API
All test users have the same password : `passwdtest`.
Their usernames are:
- Super user: `super`
- Admin: `admin`
- Student: `stu1`
- Teacher: `tea1`

A default class is also created: `L3 Informatique`.
