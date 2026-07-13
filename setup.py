from setuptools import find_packages, setup

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in edu_quality/__init__.py
from edu_quality import __version__ as version

setup(
	name="edu_quality",
	version=version,
	description="Walnut App",
	author="Hybrowlabs Technologies",
	author_email="contact@hybrowlabs.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires,
)
