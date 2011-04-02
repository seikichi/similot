from setuptools import setup, find_packages
import sys, os

version = '0.1.0'

setup(name='similot',
      version=version,
      description="",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='seikichi',
      author_email='seikichi@kmc.gr.jp',
      url='',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'tweepy',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      similot = similot:main
      """,
      )
