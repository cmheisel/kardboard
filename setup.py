from setuptools import setup, find_packages

setup(
    name="kardboard",
    version=__import__("kardboard").__version__,
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
