# GDELT Data Puller
### What is it?
It's a program that allows you to pull data from GDELT on any topic.
### Why can't I just use the [API summary](https://api.gdeltproject.org/api/v2/summary/summary)?
The summary gives you only a few articles, this gives you more. Also, you can do analysis on the data here, like in analysis.py. This should be used in conjunction with the summary.
### What are the dependencies?
First, install Python >=3.12.x. For Windows/Mac, you can do this from the [website](https://www.python.org/downloads/) (remember to select "add to path"); for Linux you can use either that or a package manager relevant to your distribution. You can also use [anaconda](https://www.anaconda.com/) or potentially some cloud tools instead.

After that, install the relevant modules, e.g. using pip (you may want to [create a virtual environment](https://docs.python.org/3/library/venv.html) first, but you don't have to):
```shell
pip install -r ./requirements.txt
```
You may also be able to use conda or your Linux distribution's package manager.
### How do I use it?
Run `python {file}.py` on the file you want to run - each file is independent and does its own thing. For `gdelt.py`, if you want to reuse an existing configuration, make sure you have a file `output/input.json`. For `summariser.py`, you need a file `urls.txt`. 
### What can I do with the code?
This code is licensed under the permissive [MIT License](LICENSE).