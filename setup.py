#!/usr/bin/env python3
import os

from setuptools import setup

BASEDIR = os.path.abspath(os.path.dirname(__file__))


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


def required(requirements_file):
    """ Read requirements file and remove comments and empty lines. """
    with open(os.path.join(BASEDIR, requirements_file), 'r') as f:
        requirements = f.read().splitlines()
        if 'MYCROFT_LOOSE_REQUIREMENTS' in os.environ:
            print('USING LOOSE REQUIREMENTS!')
            requirements = [r.replace('==', '>=').replace('~=', '>=') for r in requirements]
        return [pkg for pkg in requirements
                if pkg.strip() and not pkg.startswith("#")]


PLUGIN_ENTRY_POINT = 'ovos-tts-plugin-deepponies = ovos_tts_plugin_deepponies:DeepPoniesTTSPlugin'
SAMPLE_CONFIGS = 'ovos-tts-plugin-deepponies.config = ovos_tts_plugin_deepponies:DeepPoniesTTSPluginConfig'

setup(
    name='ovos-tts-plugin-deepponies',
    version='0.0.1',
    description='deepponies tts plugin for OpenVoiceOS',
    url='https://github.com/OpenVoiceOS/ovos-tts-plugin-deepponies',
    author='JarbasAi',
    author_email='jarbasai@mailfence.com',
    license='Apache-2.0',
    packages=['ovos_tts_plugin_deepponies'],
    install_requires=required("requirements.txt"),
    zip_safe=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Text Processing :: Linguistic',
        'License :: OSI Approved :: Apache Software License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='mycroft plugin tts OVOS OpenVoiceOS',
    entry_points={'mycroft.plugin.tts': PLUGIN_ENTRY_POINT,
                  'mycroft.plugin.tts.config': SAMPLE_CONFIGS}
)