# ==================================== Meta ==================================== #
'''
Author: Ankit Murdia
Contributors:
Version: 0.0.1
Created: 2019-11-17 12:56:21
Updated: 2019-11-17 12:56:21
Description:
Notes:
To do:
'''
# ============================================================================== #


# ================================ Dependencies ================================ #
import sys
import os
import os.path
import re
import shutil
from functools import partial
import getpass
from datetime import datetime
import time
import re

import sublime
import sublime_plugin

from . import boilerplate_settings as conf
from . import core_boiler as cb
from . import utilities
# ============================================================================== #


# ================================= Constants ================================== #
accepted_st2_resources = conf.stackstorm.keys()
modified_files = {"pack_config": (None, False)}
pack_name = None
# ============================================================================== #


# ================================= Code Logic ================================= #
#  Callable methods
def get_resource(view):
    try:
        # ext = view.file_name() and os.path.basename(view.file_name()).split('.')[-1]
        parent = view.file_name() and os.path.dirname(os.path.abspath(view.file_name())).split(os.sep)[-1].title()

        if not parent:
            raise Exception("Unable to find the resource")


        else:
            lang_obj = [k for k,v in conf.core.items() if v['ext'] == ext]
            lang = (lang_obj and lang_obj[0]) or None

        if not lang:
            raise Exception("Failed to ge the language.")

        return (lang, ext,)

    except Exception as e:
        return None

def get_resource(window_obj, resource):
    try:
        folder_list = window_obj.folders()
    except Exception as e:
        raise e

def camel_to_snake(str): 
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', str) 
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower() 


#  Abstracted classes
class PackSetupCommand(sublime_plugin.WindowCommand):
    def run(self):

        self.window.show_input_panel(
            "Enter pack path (with pack name):".format(resource),
            "",
            self.pack_setup,
            None,
            None
        )

    def pack_setup(self, pack_path):
        global pack_name

        if not os.sep in path:
            self.window.status_message("Invalid path. Please use system style path representation.")
            return False

        if not os.path.isdir(pack_path):
            create_dir = sublime.yes_no_cancel_dialog("All the intermediate directories will be created. Do you agree?".format(lang))

            if create_dir == sublime.DIALOG_YES:
                os.makdirs(pack_path)

        elif os.listdir(pack_path):
            flush_dir = sublime.yes_no_cancel_dialog("The Directory already contains other data. Do you wish to flush the directory for a new pack?".format(lang))

            if flush_dir == sublime.DIALOG_YES:
                shutil.rmtree(pack_path)
                os.makdirs(pack_path)

        pack_name = pack_path.split(os.sep)[-1]
        is_onprem = sublime.yes_no_cancel_dialog("Would you like to setup the pack on-prem?".format(lang))

        # creating pack resource directories
        for resource in accepted_st2_resources:
            if resource in ['Workflow', 'Action Chain']:
                continue

            os.makedir(os.path.join(pack_path, conf.stackstorm[resource]['dir']))

        # creating workflow directories
        os.makedir(os.path.join(pack_path, 'actions', conf.stackstorm['Workflow']['dir']))
        os.makedir(os.path.join(pack_path, 'actions', conf.stackstorm['Action Chain']['dir']))

        # creating pack config file
        fpath = os.path.join(pack_path, 'pack.yaml')
        pack_payload = {
            "pack_name": pack_name,
            "pack_author": (conf.use_system_user and getpass.getuser()) or conf.username,
            "pack_email": conf.stackstorm_config['pack']['email']
        }

        with open(fpath, 'w') as f:
            pack_config = utilities.render_template('{}/pack.bp'.format(conf.stackstorm_template_path), **payload)
            f.write(pack_config)

        pack_config_view = self.window().open_file(fpath)

        while pack_config.is_loading():
            self.window.status_message("Pack definition file is still loading.")
            time.sleep(1)

        # created pack environment config files
        for env in ['dev', 'stage', 'prod']:
            onprem_str = (is_onprem == sublime.DIALOG_YES and "_onprem") or ""
            fname = "{}{}_{}.yaml".format(pack_name, onprem_str, env)
            fpath = os.path.join(pack_path, fname)
            payload = {
                "default_cc": conf.stackstorm_config['pack_env']['{}_default_cc'.format(env)],
                "ts_format": conf.stackstorm_config['pack_env']['ts_format'],
                "env": conf.stackstorm_config['pack_env']['{}_env'.format(env)]
            }
            boilerplate = utilities.render_template('{}/yaml.bp'.format(conf.core_template_path), **payload)

            with open(fpath, "w") as f:
                f.write(boilerplate)

        # creating config schema file
        fpath = os.path.join(pack_path, 'config.schema.yaml')
        with open(fpath, 'w') as f:
            config_schema = utilities.render_template('{}/yaml.bp'.format(conf.core_template_path))
            f.write(config_schema)

        # creating requirements file
        fpath = os.path.join(pack_path, 'requirements.txt')
        with open(fpath, 'w') as f:
            f.write("")


        # opening the new pack firectory in separate window
        os.system('{} {}'.format(conf.sublime_path, pack_path))


class GetStackstormTypeCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.get_pack_name(self.window.active_view())
        self.window.show_quick_panel(accepted_st2_resources, self.get_resource_name)

    def get_resource_name(self, idx):
        try:
            resource = accepted_st2type_list[idx]
            self.window.run_command('generate_{}'.format(resource.replace('-', '_').lower()))

        except Exception as e:
            raise e

            vw = self.window.active_view()
            gen_flg = True

            if vw and vw.size() > 0:
                res = sublime.yes_no_cancel_dialog("Do you really wish to clear this tab and put {} boilerplate instead?".format(lang))

                if res != sublime.DIALOG_YES:
                    gen_flg = False

            if idx >= 0 and vw and gen_flg:
                vw.run_command("clear_page")
                vw.run_command("get_core_boilerplate", {"core_type": lang})

        except Exception as e:
            print("Error: ", e)
            pass


class GenerateSensorCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.show_input_panel(
            "Enter sensor class name:",
            "",
            self.generate_sensor_config,
            None,
            None
        )

    def generate_sensor_config(self, sensor_name):
        pass


class GenerateTriggerCommand(sublime_plugin.WindowCommand):
    def run(self):
        pass


class GenerateRuleCommand(sublime_plugin.WindowCommand):
    def run(self):
        pass


class GenerateActionCommand(sublime_plugin.WindowCommand):
    def run(self):
        pass


class GenerateWorkflowCommand(sublime_plugin.WindowCommand):
    def run(self):
        pass


class GenerateActionChainCommand(sublime_plugin.WindowCommand):
    def run(self):
        pass


class ClearPageCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.erase(edit, sublime.Region(0, self.view.size()))


class GetCoreBoilerplateCommand(sublime_plugin.TextCommand):
    def run(self, edit, core_type, params={}):
        cur_date = datetime.now().strftime(conf.ts_format)
        boiler_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), conf.core_template_path, "{}.bp".format(core_type))
        tm = Template(open(boiler_file, "r").read())
        payload = {
            'username': (conf.use_system_user and getpass.getuser()) or conf.username,
            'cur_date': cur_date
        }
        payload.update(params)
        boilerplate = tm.render(payload=payload)

        self.view.insert(edit, 0, boilerplate)
        self.view.set_syntax_file("Packages/{lang}/{lang}.tmLanguage".format(lang=core_type))
        modified[self.view.id()] = 1

# ============================================================================== #


# ================================ CLI Handler ================================= #
if __name__ == "__main__":
    pass
# ============================================================================== #