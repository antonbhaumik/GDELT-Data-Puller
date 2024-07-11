# GDELT Data Puller
### What is it?
It's a program that allows you to pull data from GDELT on any topic.
### Why can't I just use the [API summary](https://api.gdeltproject.org/api/v2/summary/summary)?
The summary doesn't give you all the articles, this does. This should be used in conjunction with the summary.
### What are the dependencies?
First, install Python >=3.12.x. For Windows/Mac, you can do this from the [website](https://www.python.org/downloads/) (remember to select "add to path"); for Linux you can use either that or a package manager relevant to your distribution. You can also use [anaconda](https://www.anaconda.com/) or potentially some cloud tools instead.

After that, install the relevant modules, e.g. using pip or conda (you may want to [create a virtual environment](https://docs.python.org/3/library/venv.html) first, but you don't have to):
```shell
pip install "googletrans==3.1.0a0" pandas requests # googletrans 3.0.0 is broken 
```
or
```shell
conda install googletrans=3.1.0a0 pandas requests # googletrans 3.0.0 is broken 
```
You may also be able to use your Linux distribution's package manager. 
### How do I use it?
Run `python main.py` (or on some Linux distributions, `python3 main.py`) in a command line, or run it in your chosen text editor or IDE, e.g. [Python IDLE](https://docs.python.org/3/library/idle.html) (comes with Python on Windows/Mac), [Spyder](https://www.spyder-ide.org/), [VSCode](https://code.visualstudio.com/) (with the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)), or [PyCharm](https://www.jetbrains.com/pycharm/).  

You will then get some prompts - fill them in and wait for a message saying the code has finished running. Read the [GDELT documentation](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/) to know what the custom options do. This program may sometimes not work - in those cases, look at the comments in the code for suggestions for fixes.
### What can I do with the code?
This code is licensed under the permissive [MIT License](LICENSE).