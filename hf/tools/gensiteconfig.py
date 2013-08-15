# -*- coding: utf-8 -*-
#
# Copyright 2012 Institut für Experimentelle Kernphysik - Karlsruher Institut für Technologie
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
An interactive, reproducible site configuration generator.

If run without arguments, this tool asks you interactively for the
basic configuration of your HappyFace site, creates the necessary
configuration files and saves the your input in an configuration file,
so you can always recreate the same base state after manual adjustments.

Always hitting enter results in a minimal configuration.
"""

import hf, sys, traceback, os, stat
try:
    import argparse
except ImportError:
    import hf.external.argparse as argparse

load_hf_environment = False

def generateConfigFiles(configuration):
    config_output = {}
    def addToSection(section, key, val):
        if not section in config_output:
            config_output[section] = {}
        config_output[section][key] = val

    def sectionToFile(directory, section, contents):
        with open(os.path.join(directory, section+'.cfg'), 'w') as f:
            f.write('\n[' + section + ']\n')
            for key, val in contents.iteritems():
                f.write(key + ' = ' + val + '\n')
    varname_to_sec_key = {
        'happyface_url': ('paths', 'happyface_url'),
        'database_url': ('database', 'database_url'),
        'web_title': ('template', 'web_title'),
        'local_happyface_cfg_dir': ('defpaths', 'local_happyface_cfg_dir'),
        'category_cfg_dir': ('paths', 'category_cfg_dir'),
        'module_cfg_dir': ('paths', 'module_cfg_dir'),
        'archive_dir': ('paths', 'archive_dir'),
        'tmp_dir': ('paths', 'tmp_dir'),
        'categories': ('happyface', 'categories'),
        'stale_data_threshold_minutes': ('happyface', 'stale_data_threshold_minutes'),
        #'auth': ('auth', ''),
        'auth.dn_file': ('auth', 'dn_file'),
        'auth.auth_script': ('auth', 'auth_script'),
        #'plotgenerator': ('', ''),
        'plotgenerator.backend': ('plotgenerator', 'backend'),
        #'apache': ('', ''),
        #'apache.cert': ('', ''),
        #'apache.cert.ca': ('', ''),
    }
    for varname, (section, key) in varname_to_sec_key.iteritems():
        if varname in configuration:
            addToSection(section, key, configuration[varname])
    if 'defpaths' in config_output:
        sectionToFile('defaultconfig/', 'paths', config_output['defpaths'])
        del config_output['defpaths']

    config_dir = configuration['local_happyface_cfg_dir'] if 'local_happyface_cfg_dir' in configuration else 'config/'
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    for section, contents in config_output.iteritems():
        sectionToFile(config_dir, section, contents)

        # set database configuration to be not world readable
    if 'database' in config_output:
        os.chmod(os.path.join(config_dir, 'database.cfg'), stat.S_IRWXU | stat.S_IRWXG)

def generateApache(configuration):
    pass

def execute():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--interactive', '-i', action='store_true', help="Ask for input. Assumed if -p is not used.")
    parser.add_argument('--no-cfg', '-n', action='store_true', help="Do not create configuration but only gather presets.")
    parser.add_argument('--presets', '-p', help="Use a file with stored presets. Can be used with -i for interactive adjustments.")
    parser.add_argument('--outfile', '-o', help="Specify a file where the presets are to be saved.")
    args = parser.parse_args()
    if args.presets == None:
        args.interactive = True

    '''
    This dictionary defines the structure of the interactive query.
    The keys are a dictionary (varname, question, type, preset) with
        varname:  The name of the configuration hint, must not contain '.'
        question: Text presented to the user
        type:     Either 'data', or 'yn' (yesno)
        preset:   The default input, presented in square brackets
    The values are dictionaries of the same type or None. If it is not None, the
    type of the corresponding key *must* be yesno, asking the user if he wants that
    feature.

    The tree represented by this dict is the flow of the interactive input generation.

    Hitting enter, to use the preset, should always result in a minimal usable
    configuration, if possible. No big magic things.
    '''
    question_structure = [
        ('happyface_url', 'Base URL of the HappyFace instance', 'data', '/', None),
        ('database_url', 'Database connection URL. Might contain plaintext passwords!', 'data', 'sqlite:///HappyFace.db', None),
        ('web_title', 'Name of the HappyFace instance', 'data', 'HappyFace Project', None),

        ('local_happyface_cfg_dir', 'Site configuration directory', 'data', 'config/', None),
        ('category_cfg_dir', 'Category configuration directory', 'data', 'config/categories-enabled/', None),
        ('module_cfg_dir', 'Module configuration directory', 'data', 'config/modules-enabled/', None),

        ('archive_dir', 'Storage path of archive directory', 'data', '%(static_dir)s/archive', None),
        ('tmp_dir', 'Temporary files path, might want to change to non-public directory', 'data', '%(static_dir)s/tmp', None),

        ('categories', 'Colon separated list of categories, may be empty', 'data', '', None),
        ('stale_data_threshold_minutes', 'Minutes to pass until data is marked stale', 'data', '60', None),

        ('auth', 'Configure authorization sources?', 'yn', 'n', [
            ('dn_file', 'Path to file with authorized DNs', 'data', '', None),
            ('auth_script', 'Path to executable authorization script', 'data', '', None),
        ]),

        ('plotgenerator', 'Do you want to use the plotgenerator?', 'yn', 'y', [
            ('backend', 'Which Matplotlib backend for HappyFace?', 'data', 'cairo.png', None),
        ]),

        #('apache', 'Do you want to create an Apache2 configuration?', 'yn', 'n', [
        #    ('cert', 'Do you want to use certificate authentication?', 'yn', 'n', [
        #        ('cacert', 'CA certificate for client certificates', 'data', '', None),
        #        ('cert', 'Server certificate file', 'data', '', None),
        #        ('key', 'Server certificate key file', 'data', '', None),
        #    ]),
        #]),
    ]
    loaded_presets = {}
    preset_output = {}

    def process_question_branch(prefix, question_list, always_set_output=False):
        for varname, question, qtype, default_preset, sub_questions in question_list:
            full_name = prefix+'.'+varname if len(prefix) > 0 else varname
            preset = loaded_presets[full_name] if full_name in loaded_presets else default_preset

            if qtype == 'yn':
                while True:
                    print question, ('(y/N) ' if preset.lower() == 'n' else '(Y/n) '),
                    answer = sys.stdin.readline()
                    if answer == '\n' or answer.lower()[:-1] in ('y', 'n', 'yes', 'no'):
                        break
                if answer == '\n':
                    answer = preset
                else:
                    answer = 'y' if answer.lower()[:-1] in ('y', 'yes') else 'n'
            elif qtype == 'data':
                print question, '['+str(preset)+']: ',
                answer = sys.stdin.readline()
                answer = preset if answer == '\n' else answer[:-1]
            else:
                print "The Universe exploded!"

            if answer != default_preset or always_set_output:
                preset_output[full_name] = answer

            if sub_questions and answer == 'y':
                process_question_branch(full_name, sub_questions, always_set_output)

    if args.presets is not None:
        with open(args.presets, 'r') as f:
            for line in f:
                if len(line) <= 1:
                    continue
                splits = line.split('=')
                var = splits[0]
                preset = '='.join(splits[1:])[:-1]
                loaded_presets[var] = preset

    if args.interactive:
        process_question_branch('', question_structure)
        site_presets = preset_output
    else:
        site_presets = loaded_presets

    if not args.no_cfg:
        generateConfigFiles(site_presets)
        if apache in site_presets and site_presets['apache'] == 'y':
            generateApache(site_presets)

    if args.outfile is None and args.interactive:
        question_structure = [
            ('preset_out', 'Save presets into file?', 'yn', 'y', [
                ('path', 'Target preset file', 'data', 'site_configuration.preset', None),
            ]),
        ]
        preset_output = {}
        process_question_branch('', question_structure, True)
        if preset_output['preset_out'] == 'y':
            args.outfile = preset_output['preset_out.path']

    if args.outfile is not None:
        with open(args.outfile, 'w') as f:
            for var, preset in site_presets.iteritems():
                f.write(str(var)+'='+str(preset)+'\n')
