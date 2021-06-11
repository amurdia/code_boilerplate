#------------------------------------ Meta ------------------------------------#
'''
Author: Ankit Murdia
Version: 0.0.1
Created: 2018-09-13 16:12:49
Updated:
Description:
Notes:
To do:
	[] option to create and save custom boiler plate
	[] option to add contributors based on the system user's full name. If the same name exists, then user should just be notified or the order of list should be altered to put the current contributor to the end of the list in order to map it to the update datetime
		[] to get the platform:
			import sys
			sys.platform
		[] to get full name in windows:
			import ctypes
 
			def get_display_name():
				GetUserNameEx = ctypes.windll.secur32.GetUserNameExW
				NameDisplay = 3
			 
				size = ctypes.pointer(ctypes.c_ulong(0))
				GetUserNameEx(NameDisplay, None, size)
			 
				nameBuffer = ctypes.create_unicode_buffer(size.contents.value)
				GetUserNameEx(NameDisplay, nameBuffer, size)
				return nameBuffer.value
		[] option to add comments to code sections like functions, classes, etc. based on the specified doc standards for the underlying language
'''
#------------------------------------------------------------------------------#


#-------------------------------- Dependencies --------------------------------#
import sublime
import sublime_plugin
from datetime import datetime
import os.path
import re
from jinja2 import Template
from . import boilerplate_settings as conf
#------------------------------------------------------------------------------#


#--------------------------------- Constants ----------------------------------#
accepted = ["py", "sql", "html", "js", "css", "sh", "yaml"]
accepted_full = ["Python", "SQL", "HTML", "JavaScript", "CSS", "Bash", "YAML"]
modified = {}
frmt_ts = r'[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}'
frmt_ver = r'[0-9]+\.[0-9]+\.[0-9]+'
# frmt_con = r'(\n\t\- (\S+ )+)*'
pat_ts = r'\s*Updated: ' + frmt_ts
pat_ts2 = r'\s*Created: ' + frmt_ts
pat_ver = r'\s*Version: ' + frmt_ver
# pat_con = r'(?s)\s*Contributors:' + frmt_con
pattern = {
			"py": "^{}$",
			"sql": "^--{}$",
			"html": "^{}$",
			"js": "^{}$",
			"css": "^{}$",
			"sh": "^#{}$",
			"yaml": "^#{}$"
		}
section = {
			"py": ["#,#", "#,#"],
			"sql": ["--,", "--,"],
			"html": ["<!--,-->", "<!--,-->"],
			"js": ["//,//", "//,//"],
			"css": ["/*,", "  ,*/"],
			"sh": ["#,#", "#,#"],
			"yaml": ["#,#", "#,#"]
		}
#------------------------------------------------------------------------------#


def get_extension(view):
	try:
		ext = view.file_name() and os.path.basename(view.file_name()).split('.')[-1]

		if not ext:
			lang = os.path.basename(view.settings().get('syntax')).split('.')[0]
			ext = accepted[accepted_full.index(lang)]

		# if view.find(pattern[ext].format(pat_ver), 0, sublime.IGNORECASE):
		return ext

	except Exception as e:
		return None

#---------------------------- Generate boilerplate ----------------------------#
class BoilerTypeCommand(sublime_plugin.WindowCommand):
	def run(self):
		ext = get_extension(self.window.active_view())

		if not ext:
			self.window.show_quick_panel(accepted_full, self.get_boiler)

		elif ext in accepted:
			self.get_boiler(accepted.index(ext))
		
		else:
			self.window.status_message(".{} is not yet supported.".format(ext))

	def get_boiler(self, idx):
		try:
			vw = self.window.active_view()
			gen_flg = True

			if vw and vw.size() > 0:
				res = sublime.yes_no_cancel_dialog("Do you really wish to clear this tab and put {} boilerplate instead?".format(accepted_full[int(idx)]))

				if res != sublime.DIALOG_YES:
					gen_flg = False

			if idx >= 0 and vw and gen_flg:
				vw.run_command("clear_page")
				vw.run_command("boiler_plate", {"bp": accepted[idx]})

		except Exception as e:
			print("Error: ", e)
			pass

class ClearPageCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.view.erase(edit, sublime.Region(0, self.view.size()))

class BoilerPlateCommand(sublime_plugin.TextCommand):
	def run(self, edit, bp, fformat=None, params={}):
		# boiler_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "{}.bp".format(bp))
		# boilerplate = open(boiler_file, "r").read()
		# cur_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		# boilerplate = re.sub(r'{{username}}', conf.username, boilerplate)
		# boilerplate = re.sub(r'{{cur_date}}', cur_date, boilerplate)
		cur_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		boiler_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "{}.bp".format(bp))
		tm = Template(open(boiler_file, "r").read())
		payload = {
			'username': conf.username,
			'cur_date': cur_date
		}
		payload.update(params)
		boilerplate = tm.render(payload=payload)

		self.view.insert(edit, 0, boilerplate)
		lang = (fformat and accepted_full[fformat]) or accepted_full[accepted.index(bp)]
		self.view.set_syntax_file("Packages/{lang}/{lang}.tmLanguage".format(lang=lang))
		modified[self.view.id()] = 1

#------------------------------------------------------------------------------#


#------------------------------ Update timestamp ------------------------------#
class UpdateCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		ext = get_extension(self.view)
		region = self.view.find(pattern[ext].format(pat_ts), 0, sublime.IGNORECASE)

		if not region:
			self.window.status_message("Please create a boilerplate first: <ctrl> + <alt> + a")
			return
				
		reg_str = re.sub(frmt_ts, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.view.substr(region))
		self.view.replace(edit, region, reg_str)
		# self.view.run_command("contribute")

class EventDump(sublime_plugin.EventListener):
	def on_load(self, view):
		ext = get_extension(view)
		sz = view.size()

		if ext and ext in accepted and sz > 0:
			modified[view.id()] = 0

	def on_modified(self, view):
		if modified.get(view.id(), -1) == 0:
			modified[view.id()] = 1
	
	def on_pre_save(self, view):
		if modified.get(view.id(), -1) > 0:
			view.run_command("update")
			modified[view.id()] = 0

	def on_pre_close(self, view):
		modified.pop(view.id(), None)
#------------------------------------------------------------------------------#


#------------------------------- Update version -------------------------------#
class VersionIncrementCommand(sublime_plugin.WindowCommand):
	def run(self):
		vw = self.window.active_view()
		ext = get_extension(vw)

		if not ext:
			# self.window.active_view().show_popup("<p>Please create a boilerplate first: &lt;ctrl&gt; + &lt;alt&gt; + a</p>", sublime.HIDE_ON_MOUSE_MOVE_AWAY)
			self.window.status_message("Please create a boilerplate first: <ctrl> + <alt> + a")
			return

		self.window.show_quick_panel(["Major version", "Minor version", "Patch version", "Custom version"], self.update_version)

	def update_version(self, idx):
		try:
			vw = self.window.active_view()
			ext = get_extension(vw)
			region = vw.find(pattern[ext].format(pat_ver), 0, sublime.IGNORECASE)

			if not region:
				self.window.status_message("Please create a boilerplate first: <ctrl> + <alt> + a")
				return

			reg_str = vw.substr(region)
			ver_str = re.findall(frmt_ver, reg_str)[0]

			if idx == 3:
				self.window.run_command("custom_version", {"cur_ver": ver_str})
				return
			
			version = list(map(int, ver_str.split(".")))
			version[idx] += 1
			new_ver_str = ".".join(map(str, version))
			vw.run_command("update_version", {"ver_str": new_ver_str})

		except Exception as e:
			print("[VersionIncrementCommand] Error: ", e)
			pass

class CustomVersionCommand(sublime_plugin.WindowCommand):
	def run(self, cur_ver):
		self.window.show_input_panel("Enter version:", cur_ver, self.update_version, None, None)

	def update_version(self, ver_str):
		try:
			vw = self.window.active_view()

			if re.match(frmt_ver, ver_str.strip()):
				vw.run_command("update_version", {"ver_str": ver_str})
			else:
				# self.window.run_command("custom_version", {"cur_ver": "Invalid version format: {} (correct format: <major>.<minor>.<patch>)".format(ver_str.strip())})
				self.window.status_message("Invalid version format: {} (correct format: <major>.<minor>.<patch>)".format(ver_str.strip()))
				self.window.run_command("custom_version", {"cur_ver": ""})

		except Exception as e:
			print("Error: ", e)
			pass

class UpdateVersionCommand(sublime_plugin.TextCommand):
	def run(self, edit, ver_str):
		ext = get_extension(self.view)
		region = self.view.find(pattern[ext].format(pat_ver), 0, sublime.IGNORECASE)
		reg_str = re.sub(frmt_ver, ver_str.strip(), self.view.substr(region))
		self.view.replace(edit, region, reg_str)
#------------------------------------------------------------------------------#


#---------------------------- Generate new section ----------------------------#
class SectionTitleCommand(sublime_plugin.WindowCommand):
	def run(self):
		vw = self.window.active_view()
		ext = get_extension(vw)

		if not ext:
			# vw.show_popup("<p>Please create a boilerplate first: &lt;ctrl&gt; + &lt;alt&gt; + a</p>", sublime.HIDE_ON_MOUSE_MOVE_AWAY)
			self.window.status_message("Please create a boilerplate first: <ctrl> + <alt> + a")
			return

		self.window.show_input_panel("Enter section title:", "New Section", self.create_section, None, None)

	def create_section(self, sec_title):
		try:
			self.window.active_view().run_command("code_section", {"sec_title":str(sec_title)})

		except Exception as e:
			print("Error: ", e)
			pass

class CodeSectionCommand(sublime_plugin.TextCommand):
	def run(self, edit, sec_title, data=None):
		title_len = len(sec_title.strip())
		pre_len = (76 - title_len) // 2
		post_len = (76 - title_len + (title_len % 2)) // 2
		data_str = (data and str(data)) or ""
		ext = get_extension(self.view)

		secstr = "\n{delim1} {title} {delim2}\n{data}\n{delim3}\n".format(
						title = sec_title.strip(),
						delim1 = section[ext][0].split(',')[0] + ' ' + pre_len*'=',
						delim2 = post_len*'=' + ' ' + section[ext][0].split(',')[1],
						delim3 = section[ext][1].split(',')[0] + ' ' + 78*"=" + ' ' + section[ext][1].split(',')[1],
						data = data_str
					)
		sels = self.view.sel()
		cur_reg = sels[0]
		new_reg = self.view.expand_by_class(cur_reg.end(), sublime.CLASS_EMPTY_LINE
 | sublime.CLASS_LINE_START | sublime.CLASS_LINE_END)
		self.view.insert(edit, new_reg.end(), secstr)
#------------------------------------------------------------------------------#


#---------------------------- Update contributors -----------------------------#
# class ContributeCommand(sublime_plugin.WindowCommand):
# 	def run(self):
# 		vw = self.window.active_view()
# 		ext = get_extension(vw)

# 		if not ext:
# 			# self.window.active_view().show_popup("<p>Please create a boilerplate first: &lt;ctrl&gt; + &lt;alt&gt; + a</p>", sublime.HIDE_ON_MOUSE_MOVE_AWAY)
# 			self.window.status_message("Please create a boilerplate first: <ctrl> + <alt> + a")
# 			return

# 		self.window.show_quick_panel(["Major version", "Minor version", "Patch version", "Custom version"], self.update_version)

# 	def update_version(self, idx):
# 		try:
# 			vw = self.window.active_view()
# 			ext = get_extension(vw)
# 			region = vw.find(pattern[ext].format(pat_con), 0, sublime.IGNORECASE)

# 			if not region:
# 				self.window.status_message("Please create a boilerplate first: <ctrl> + <alt> + a")
# 				return

# 			reg_str = vw.substr(region)
# 			ver_str = re.findall(frmt_ver, reg_str)[0]

# 			if idx == 3:
# 				self.window.run_command("custom_version", {"cur_ver": ver_str})
# 				return
			
# 			version = list(map(int, ver_str.split(".")))
# 			version[idx] += 1
# 			new_ver_str = ".".join(map(str, version))
# 			vw.run_command("update_version", {"ver_str": new_ver_str})

# 		except Exception as e:
# 			print("[VersionIncrementCommand] Error: ", e)
# 			pass

# class CustomVersionCommand(sublime_plugin.WindowCommand):
# 	def run(self, cur_ver):
# 		self.window.show_input_panel("Enter version:", cur_ver, self.update_version, None, None)

# 	def update_version(self, ver_str):
# 		try:
# 			vw = self.window.active_view()

# 			if re.match(frmt_ver, ver_str.strip()):
# 				vw.run_command("update_version", {"ver_str": ver_str})
# 			else:
# 				# self.window.run_command("custom_version", {"cur_ver": "Invalid version format: {} (correct format: <major>.<minor>.<patch>)".format(ver_str.strip())})
# 				self.window.status_message("Invalid version format: {} (correct format: <major>.<minor>.<patch>)".format(ver_str.strip()))
# 				self.window.run_command("custom_version", {"cur_ver": ""})

# 		except Exception as e:
# 			print("Error: ", e)
# 			pass

# class UpdateVersionCommand(sublime_plugin.TextCommand):
# 	def run(self, edit, ver_str):
# 		ext = get_extension(self.view)
# 		region = self.view.find(pattern[ext].format(pat_ver), 0, sublime.IGNORECASE)
# 		reg_str = re.sub(frmt_ver, ver_str.strip(), self.view.substr(region))
# 		self.view.replace(edit, region, reg_str)
#------------------------------------------------------------------------------#