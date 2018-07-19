This repo contains some toy code and a Jupyter notebook that demonstrates how one could build a very basic blockchain using the same core technologies that full implementations (like Bitcoin) might use. The purpose is to help get a deeper understand of blockchain, experiment with it, and to have fun in exploration.

This code and the notebooks were originally used as part of a [live-coding session][1] at the O'Reilly Open Source Convention 2018 in Portland, Oregon.

Please see the LICENSE file for copyright and usage information.

[1]: https://conferences.oreilly.com/oscon/oscon-or/public/schedule/detail/66678

## Usage

Included is a `Pipfile` and `requirements.txt` that can be used by `pipenv` or `pip` to setup your environment. Other tools can be used as long as Python 3.7, and the other dependencies mentioned in the `Pipfile`, are installed.

Using `pipenv`:

```
cd <CLONED DIR>
pipenv install
pipenv shell
python blockchain.py # Run the example code
jupyter notebook # Launch Jupyter (installed by pipenv) so you can experiment with code there. This will open a browser automatically.
```
