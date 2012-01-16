"""GitHub flavoured markdown: because normal markdown has some vicious
gotchas.

Further reading on the gotchas:
http://blog.stackoverflow.com/2009/10/markdown-one-year-later/

This is a Python port of GitHub code, taken from
https://gist.github.com/901706

To run the tests, install nose ($ easy_install nose) then:

$ nosetests libs/gfm.py

"""

import re


def remove_pre_blocks(markdown_source):
    # replace <pre> blocks with placeholders, so we don't accidentally
    # muck up stuff inside the block with our other transformations
    original_blocks = []

    pattern = re.compile(r'<pre>.*?</pre>', re.MULTILINE | re.DOTALL)

    while re.search(pattern, markdown_source):
        # save the original block
        original_block = re.search(pattern, markdown_source).group(0)
        original_blocks.append(original_block)

        # put in a placeholder
        markdown_source = re.sub(pattern, '{placeholder}', markdown_source,
                                 count=1)

    return (markdown_source, original_blocks)


def remove_inline_code_blocks(markdown_source):
    original_blocks = []

    pattern = re.compile(r'`.*?`', re.DOTALL)

    while re.search(pattern, markdown_source):
        # save the original block
        original_block = re.search(pattern, markdown_source).group(0)
        original_blocks.append(original_block)

        # put in a placeholder
        markdown_source = re.sub(pattern, '{placeholder}', markdown_source,
                                 count=1)

    return (markdown_source, original_blocks)


def gfm(text):
    text, code_blocks = remove_pre_blocks(text)
    text, inline_blocks = remove_inline_code_blocks(text)

    # Prevent foo_bar_baz from ending up with an italic word in the middle.
    def italic_callback(matchobj):
        s = matchobj.group(0)
        # don't mess with URLs:
        if 'http:' in s or 'https:' in s:
            return s

        return s.replace('_', '\_')

    # fix italics for code blocks
    pattern = re.compile(r'^(?! {4}|\t).*\w+(?<!_)_\w+_\w[\w_]*', re.MULTILINE | re.UNICODE)
    text = re.sub(pattern, italic_callback, text)

    # linkify naked URLs
    regex_string = """
(^|\s) # start of string or has whitespace before it
(https?://[:/.?=&;a-zA-Z0-9_-]+) # the URL itself, http or https only
(\s|$) # trailing whitespace or end of string
"""
    pattern = re.compile(regex_string, re.VERBOSE | re.MULTILINE | re.UNICODE)

    # wrap the URL in brackets: http://foo -> [http://foo](http://foo)
    text = re.sub(pattern, r'\1[\2](\2)\3', text)

    # In very clear cases, let newlines become <br /> tags.
    def newline_callback(matchobj):
        if len(matchobj.group(1)) == 1:
            return matchobj.group(0).rstrip() + '  \n'
        else:
            return matchobj.group(0)

    pattern = re.compile(r'^[\w\<][^\n]*(\n+)', re.MULTILINE | re.UNICODE)
    text = re.sub(pattern, newline_callback, text)

    # now restore removed code blocks
    removed_blocks = code_blocks + inline_blocks
    for removed_block in removed_blocks:
        text = text.replace('{placeholder}', removed_block, 1)

    return text

# Test suite.
try:
    from nose.tools import assert_equal
except ImportError:
    def assert_equal(a, b):
        assert a == b, '%r != %r' % (a, b)

def test_single_underscores():
    """Don't touch single underscores inside words."""
    assert_equal(
        gfm('foo_bar'),
        'foo_bar',
    )

def test_underscores_code_blocks():
    """Don't touch underscores in code blocks."""
    assert_equal(
        gfm('    foo_bar_baz'),
        '    foo_bar_baz',
    )

def test_underscores_inline_code_blocks():
    """Don't touch underscores in code blocks."""
    assert_equal(
        gfm('foo `foo_bar_baz`'),
        'foo `foo_bar_baz`',
    )

def test_underscores_pre_blocks():
    """Don't touch underscores in pre blocks."""
    assert_equal(
        gfm('<pre>\nfoo_bar_baz\n</pre>'),
        '<pre>\nfoo_bar_baz\n</pre>',
    )

def test_pre_block_pre_text():
    """Don't treat pre blocks with pre-text differently."""
    a = '\n\n<pre>\nthis is `a\\_test` and this\\_too\n</pre>'
    b = 'hmm<pre>\nthis is `a\\_test` and this\\_too\n</pre>'
    assert_equal(
        gfm(a)[2:],
        gfm(b)[3:],
    )

def test_two_underscores():
    """Escape two or more underscores inside words."""
    assert_equal(
        gfm('foo_bar_baz'),
        'foo\\_bar\\_baz',
    )
    assert_equal(
        gfm('something else then foo_bar_baz'),
        'something else then foo\\_bar\\_baz',
    )

def test_newlines_simple():
    """Turn newlines into br tags in simple cases."""
    assert_equal(
        gfm('foo\nbar'),
        'foo  \nbar',
    )

def test_newlines_group():
    """Convert newlines in all groups."""
    assert_equal(
        gfm('apple\npear\norange\n\nruby\npython\nerlang'),
        'apple  \npear  \norange\n\nruby  \npython  \nerlang',
    )

def test_newlines_long_group():
    """Convert newlines in even long groups."""
    assert_equal(
        gfm('apple\npear\norange\nbanana\n\nruby\npython\nerlang'),
        'apple  \npear  \norange  \nbanana\n\nruby  \npython  \nerlang',
    )

def test_newlines_list():
    """Don't convert newlines in lists."""
    assert_equal(
        gfm('# foo\n# bar'),
        '# foo\n# bar',
    )
    assert_equal(
        gfm('* foo\n* bar'),
        '* foo\n* bar',
    )

def test_underscores_urls():
    """Don't replace underscores in URLs"""
    assert_equal(
        gfm('[foo](http://example.com/a_b_c)'),
        '[foo](http://example.com/a_b_c)'
        )

def test_underscores_in_html():
    """Don't replace underscores in HTML blocks"""
    assert_equal(
        gfm('<img src="http://example.com/a_b_c" />'),
        '<img src="http://example.com/a_b_c" />'
        )

def test_linkify_naked_urls():
    """Wrap naked URLs in []() so they become clickable links."""
    assert_equal(
        gfm(" http://www.example.com:80/foo?bar=bar&biz=biz"),
        " [http://www.example.com:80/foo?bar=bar&biz=biz](http://www.example.com:80/foo?bar=bar&biz=biz)"
        )
