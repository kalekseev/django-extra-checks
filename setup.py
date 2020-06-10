from __future__ import absolute_import

import io
import os
from glob import glob

from setuptools import find_packages, setup


def read(*names, **kwargs):
    return io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8"),
    ).read()


setup(
    name="django-extra-checks",
    version="0.1.0a0",
    description="Collection of useful checks for Django Checks Frameworks",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="Konstantin Alekseev",
    author_email="mail@kalekseev.com",
    url="https://github.com/kalekseev/django-extra-checks",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[
        os.path.splitext(os.path.basename(path))[0] for path in glob("src/*.py")
    ],
    include_package_data=True,
    zip_safe=False,
    extras_require={"dev": ["pytest", "pytest-django", "pytest-cov", "Django"]},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords=["django", "checks"],
)
