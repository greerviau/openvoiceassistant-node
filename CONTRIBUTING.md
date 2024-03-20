# How to contribute

It is encouraged for users to make contributions to improve the software for themselves and others.

## Getting Started

Join the [Discord](https://discord.gg/3bZuq9QzFk)

### Setup Dev Environment

Fork the repo.

Clone your fork of the repo.

Inside your repo run:
```
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```
You should then be able to run the node.
```
python -m node
```
When developing you can utilize some of the aditional flags such as ```--debug```, ```--no_sync```, ```--sync_up```, ```--port``` and ```--hub_port```<br>
```--debug``` will give you more log info.<br>
```--no_sync``` will not sync with the hub, this might be usefull if you are not running a hub instance but want to test if the node starts.<br>
```--sync_up``` will force push up the configuration present on the node to the hub as opposed to pulling configuration from the hub down to the node.<br>
```--debug``` will give you more log info.<br>
```--hub_ip``` will change the hub port that the node expects the hub api runs on. It is recomended not to change this unless you have a specific use case.<br>
```--hub_port``` will change the hub port that the node expects the hub api runs on. It is recomended not to change this unless you have a specific use case.<br>
```--port``` will change the port that the node api runs on. It is recomended not to change this unless you have a specific use case.

From here you should be able to make changes and test them.

If you are making changes that require updates to ```requirements.txt```, you must use ```pip freeze``` and make the appropriate changes. Make sure to update it for ```requirements.txt``` and ```requirements_dev.txt```.

## General Improvements

Documentation coming soon... (Or just read the code)

## Pull Requests

Pull requests should be against the develop branch. If you're unsure about a contribution, feel free to open a discussion, issue, or draft PR to discuss the problem you're trying to solve.

A good pull request has all of the following:
* a clearly stated purpose
* every line changed directly contributes to the stated purpose
* verification, i.e. how did you test your PR?
* justification
  * if you've optimized something, post benchmarks to prove it's better