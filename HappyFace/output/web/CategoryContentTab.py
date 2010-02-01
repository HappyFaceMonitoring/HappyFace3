import sys, os

from HTMLOutput import *
from CategoryFastNavigation import *

class CategoryContentTab(HTMLOutput):
    def __init__(self,cat_content,config,category,cat_id,timestamp):
	HTMLOutput.__init__(self, 4)

	fast_nav = CategoryFastNavigation(category).output

	# a few symbols / hyperlinks for the status bar ;-)
	valid_xhtml11 = """
	<a href="http://validator.w3.org/check?uri=referer"><img style="border:0;vertical-align: middle;" src="config/images/valid-xhtml11.png" alt="Valid XHTML 1.1" /></a>
	"""
	valid_css = """
	<a href="http://jigsaw.w3.org/css-validator/check/referer?&amp;profile=css3"><img style="border:0;vertical-align: middle;" src="config/images/vcss.gif" alt="Valid CSS!" /></a>
	"""
	python = """
	<a href="http://python.org"><img style="border:0;vertical-align: middle;" src="config/images/python_logo_mini.png" alt="Python" /></a>
	"""
	sqlite = """
	<a href="http://sqlite.org"><img style="border:0;vertical-align: middle;" src="config/images/sqlite_logo_mini.png" alt="SQLite" /></a>
	"""
	php = """
	<a href="http://php.net"><img style="border:0;vertical-align: middle;" src="config/images/php_logo_mini.png" alt="PHP" /></a>
	"""

	mc_begin = []
	mc_begin.append('<div class="HappyPanelsContent">')

	mc_end = []
	mc_end.append(' <div>')
	mc_end.append('  ' + valid_xhtml11.strip())
	mc_end.append('  ' + valid_css.strip())
	mc_end.append('  ' + python.strip())
	mc_end.append('  ' + sqlite.strip())
	mc_end.append('  ' + php.strip())
	mc_end.append(' </div>')
	mc_end.append('</div>')

	output = "<?php $category_id='" + str(cat_id) + "';?>"

	output += self.PHPArrayToString(mc_begin)
	output += fast_nav + "\n"
	output += cat_content + "\n"
	output += self.PHPArrayToString(mc_end)

        self.output = output
