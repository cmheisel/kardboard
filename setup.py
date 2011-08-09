import os
from setuptools import setup, find_packages

this_folder = os.path.dirname(os.path.abspath(__file__))
version_file = os.path.join(this_folder, 'kardboard', 'VERSION')

setup(
    name="kardboard",
    version=file(version_file, 'r').read(),
    author="Chris Heisel",
    author_email="chris@heisel.org",
    description=("Dashboard for tracking real-life cards on a real-life Kanban board(s)"),
    long_description=open("README.rst").read(),
    url="https://github.com/cmheisel/kardboard",
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Framework :: Flask",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
    ]
)
