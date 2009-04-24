import sys, os

class CategoryContentTab(object):
    def __init__(self,cat_content,timestamp):

	# a few symbols / hyperlinks for the status bar ;-)
	valid_xhtml11 = """
	<a href="http://validator.w3.org/check?uri=referer"><img style="border:0;vertical-align: middle;" src="config/valid-xhtml11.png" alt="Valid XHTML 1.1" /></a>
	"""
	valid_css = """
	<a href="http://jigsaw.w3.org/css-validator/check/referer"><img style="border:0;vertical-align: middle;" src="config/vcss.gif" alt="Valid CSS!" /></a>
	"""
	python = """
	<a href="http://python.org"><img style="border:0;vertical-align: middle;" src="config/python_logo_mini.png" alt="Python" /></a>
	"""
	sqlite = """
	<a href="http://sqlite.org"><img style="border:0;vertical-align: middle;" src="config/sqlite_logo_mini.png" alt="SQLite" /></a>
	"""
	php = """
	<a href="http://php.net"><img style="border:0;vertical-align: middle;" src="config/php_logo_mini.png" alt="PHP" /></a>
	"""

	output = ""

        output += '<div class="TabbedPanelsContent"><br/>' + "\n"
        output += cat_content + "\n"
        output += valid_xhtml11 + valid_css + python + sqlite + php + "\n"
	output += '</div>' + "\n"

        self.output = output

