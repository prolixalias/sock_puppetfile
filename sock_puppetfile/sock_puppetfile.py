"""Main module."""

import sys
import requests
import re
import json
import logging
import difflib

forgeapi_url = "https://forgeapi.puppet.com/v3/modules"
module_pattern = re.compile(r"^mod\s+'(\w{1,32}-\w{1,32})',\s*'(\d{1,3}.\d{1,3}.\d{1,3})'")
input_module_list = {}
output_module_list = {}

class SockPuppetfile():

    def __init__(self, path):
        self.puppetfile = path
        self.puppetfile_contents = {}
        self.new_puppetfile_contents = []
        self.input_module_list = {}
        self.output_module_list = {}
        self.delta = []

    def get_dependencies(self, slug_parent, slug_dependency, output_module_list):

        slug_dependency = slug_dependency.replace('/', '-', 1)

        query_params = {'exclude_fields': 'uri name downloads created_at updated_at deprecated_at deprecated_for superseded_by supported endorsement module_group owner releases feedback_score homepage_url issues_url readme changelog license reference'}
        d = requests.get(f"{forgeapi_url}/{slug_dependency}", params = query_params)
        d_response = d.json()

        self.output_module_list |= {d_response['slug']: d_response['current_release']['version']}

        if d_response['current_release']['metadata']['dependencies']:
            for new_dependency in d_response['current_release']['metadata']['dependencies']:
                self.get_dependencies(d_response['slug'], new_dependency['name'], output_module_list)
        else:
            self.output_module_list |= {d_response['slug']: d_response['current_release']['version']}

    def get_input_hash(self):
        for i, line in enumerate(open(self.puppetfile)):
            for match in re.finditer(module_pattern, line):
                logging.info('found semver module on line %s - %s' % (i+1, match.group(1)))
                self.input_module_list[match.group(1)] = match.group(2)
        return self.input_module_list
 
    def get_output_hash(self):
        for module in self.input_module_list:
            query_params = {'exclude_fields': 'uri name downloads created_at updated_at deprecated_at deprecated_for superseded_by supported endorsement module_group owner releases feedback_score homepage_url issues_url readme changelog license reference'}
            r = requests.get(f"{forgeapi_url}/{module}", params = query_params)
            response = r.json()

            logging.debug(f"response: {json.dumps(response, indent = 4)}")
            self.output_module_list |= {response['slug']: response['current_release']['version']}

            if response['current_release']['metadata']['dependencies']:
                for initial_dependency in response['current_release']['metadata']['dependencies']:
                    self.get_dependencies(response['slug'], initial_dependency['name'], output_module_list)
            else:
                self.output_module_list |= {response['slug']: response['current_release']['version']}
        return self.output_module_list

    def get_puppetfile_contents(self):
        source_puppetfile = open(self.puppetfile, "r")
        self.puppetfile_contents = source_puppetfile.readlines()
        return self.puppetfile_contents

    def generate_new_puppetfile(self):
        for line in self.puppetfile_contents:
            if re.match(module_pattern, line):
                for match in re.finditer(module_pattern, line):
                    for module, version in self.output_module_list.items():
                        if module == match.group(1):
                            line = re.sub(match.group(2), version, line)
                            # print(f"new line: {line}")
                            self.new_puppetfile_contents.append(line)
            else:
                # print(f"original line: {line}")
                self.new_puppetfile_contents.append(line)
        # print(f"new puppetfile contents: {self.new_puppetfile_contents}")
        return self.new_puppetfile_contents

    def compare_puppetfiles(self):
        original_puppetfile = self.puppetfile_contents
        resulting_puppetfile = self.new_puppetfile_contents
        self.delta = difflib.unified_diff(original_puppetfile, resulting_puppetfile)
        return self.delta