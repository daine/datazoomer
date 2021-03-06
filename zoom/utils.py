# Copyright (c) 2005-2011 Dynamic Solutions Inc. (support@dynamic-solutions.com)
#
# This file is part of DataZoomer.
#
# DataZoomer is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# DataZoomer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Utilities that rely only on standard python libraries"""

import os
import string
import collections
import ConfigParser
from sys import version_info

norm = string.maketrans('','')
special = string.translate(norm, norm, string.letters + string.digits + ' ')
PY2 = version_info[0] == 2

def trim(text):
    """
        Remove the left most spaces for markdown

        >>> trim('remove right ')
        'remove right'

        >>> trim(' remove left')
        'remove left'

        >>> trim(' remove spaces \\n    from block\\n    of text ')
        'remove spaces\\n   from block\\n   of text'

    """
    n = 0
    for line in text.splitlines():
        if line.isspace():
            continue
        if line.startswith(' '):
            n = len(line) - len(line.lstrip())
            break
    if n:
        lines = []
        for line in text.splitlines():
            lines.append(line[n:].rstrip())
        return '\n'.join(lines)
    else:
        return text.strip()

def name_for(text):
    """Calculates a valid HTML field name given an arbitrary string."""
    return text.replace('*','').replace(' ','_').strip().upper()

def id_for(*args):
    """
    Calculates a valid HTML tag id given an arbitrary string.

        >>> id_for('Test 123')
        'test-123'
        >>> id_for('New Record')
        'new-record'
        >>> id_for('New "special" Record')
        'new-special-record'
        >>> id_for("hi", "test")
        'hi~test'
        >>> id_for("hi test")
        'hi-test'
        >>> id_for(1234)
        '1234'

    """
    def id_(text):
        return str(text).strip().translate(norm, special).lower().replace(' ','-')

    return '~'.join([id_(arg) for arg in args])

def tag_for(tag_text,content='',*args,**keywords):
    """
    Builds an HTML tag.

        deprecated : use html.tag instead
    
        >>> tag_for('a',href='http://www.google.com')
        '<A HREF="http://www.google.com" />'
    
    """
    tag_type = tag_text.upper()
    singles = ''.join([' %s' % arg.upper() for arg in args])
    attribute_text = ''.join([' %s="%s"' % (key.upper(),keywords[key]) for key in keywords])
    if content or tag_type.lower() in ['textarea']:
        return '<%s%s%s>%s</%s>' % (tag_type,singles,attribute_text,content,tag_type)
    else:
        return '<%s%s%s />' % (tag_type,singles,attribute_text)

def layout_field(label,content,edit=True):
    """
    Layout a field (usually as part of a form).

        >>> layout_field('Name','<input type=text value="John Doe">',True)
        '<div class="field"><div class="field_label">Name</div><div class="field_edit"><input type=text value="John Doe"></div></div>'

        >>> layout_field('Name','John Doe',False)
        '<div class="field"><div class="field_label">Name</div><div class="field_show">John Doe</div></div>'

    """
    if edit:
        tpl = """<div class="field"><div class="field_label">%(label)s</div><div class="field_edit">%(content)s</div></div>"""
    else:
        tpl = """<div class="field"><div class="field_label">%(label)s</div><div class="field_show">%(content)s</div></div>"""
    return tpl % (dict(label=label,content=content))

def matches(item, terms):
    if not terms: return True
    v = [str(i).lower() for i in item.values()]
    return all(any(t in s for s in v) for t in terms)

def search(items, text):
    search_terms = list(set([i.lower() for i in text.strip().split()]))
    for item in items:
        if matches(item, search_terms):
            yield item

def kind(o):
    """
    returns a suitable table name for an object based on the object class
    """
    n = []
    for c in o.__class__.__name__:
        if c.isalpha() or c=='_':
            if c.isupper() and len(n):
                n.append('_')
            n.append(c.lower())
    return ''.join(n)

class Storage(dict):
    """
    A Storage object is like a dictionary except `obj.foo` can be used
    in addition to `obj['foo']`.

        >>> o = Storage(a=1)
        >>> o.a
        1
        >>> o['a']
        1
        >>> o.a = 2
        >>> o['a']
        2
        >>> del o.a
        >>> o.a
        Traceback (most recent call last):
            ...
        AttributeError: 'a'

    """
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError, k:
            raise AttributeError, k

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError, k:
            raise AttributeError, k

    def __repr__(self):
        return '<Storage ' + dict.__repr__(self) + '>'

class Record(Storage):
    """
    A dict with attribute access to items, attributes and properties

        >>> class Foo(Record):
        ...     full = property(lambda a: a.fname + ' ' + a.lname)
        ...
        >>> f = Foo(fname='Joe', lname='Smith')
        >>> f.full
        'Joe Smith'
        >>> f['full']
        'Joe Smith'
        >>> 'The name is %(full)s' % f
        'The name is Joe Smith'
        >>> print f
        Foo
          fname ...............: 'Joe'
          lname ...............: 'Smith'
          full ................: 'Joe Smith'

        >>> f.attributes()
        ['fname', 'lname', 'full']

        >>> class FooBar(Record):
        ...     full = property(lambda a: a.fname + ' ' + a.lname)
        ...
        >>> o = FooBar(a=2)
        >>> kind(o)
        'foo_bar'
        >>> o.a
        2
        >>> o['a']
        2
        >>> o.double = property(lambda o: 2*o.a)
        >>> o.double
        4
        >>> o['double']
        4
        >>> del o.a
        >>> o.a
        Traceback (most recent call last):
            ...
        AttributeError: 'a'

        >>> class Foo(Record):
        ...     full = property(lambda a: a.fname + ' ' + a.lname)
        ...
        >>> f = Foo(fname='Joe', lname='Smith')
        >>> f.full
        'Joe Smith'
        >>> f['full']
        'Joe Smith'
        >>> 'The name is %(full)s' % f
        'The name is Joe Smith'
        >>> getattr(f,'full')
        'Joe Smith'

        >>> o = Record(a=2)
        >>> o.a
        2
        >>> o['a']
        2
        >>> o.double = property(lambda o: 2*o.a)
        >>> o.double
        4
        >>> o['double']
        4
        >>> del o.a
        >>> o.a
        Traceback (most recent call last):
            ...
        AttributeError: 'a'

    """

    def attributes(self):
        all_keys = self.keys() + [k for k,v in self.__class__.__dict__.items() if hasattr(v,'__get__')]
        special_keys = 'id', 'key', 'name', 'title', 'description', 'first_name', 'middle_name', 'last_name', 'fname', 'lname'
        result = []
        for key in special_keys:
            if key in all_keys:
                result.append(key)
        for key in sorted(all_keys):
            if not key in special_keys:
                result.append(key)
        return result

    def valid(self):
        return 1

    def allows(self, user, action):
        return True

    def __getitem__(self, name):
        try:
            value = dict.__getitem__(self, name)
            if hasattr(value, '__get__'):
                return value.__get__(self)
            else:
                return value
        except KeyError, k:
            try:
                return self.__class__.__dict__[name].__get__(self)
            except KeyError, k:
                raise

    def __str__(self):
        return self.__repr__(pretty=True)

    def __repr__(self, pretty=False):

        name = self.__class__.__name__
        attributes = self.attributes()
        t = []

        items = [(key, self[key]) for key in attributes if not key.startswith('_')]

        if pretty:
            for key, value in items:
                if callable(value):
                    v = value()
                else:
                    v = value
                t.append('  %s %s: %s'  % (key,'.'*(20-len(key[:20])), repr(v)))
            return '\n'.join([name] + t)

        else:
            for key, value in items:
                if callable(value):
                    v = value()
                else:
                    v = value
                t.append((repr(key), repr(v)))
            return '<%s {%s}>' % (name, ', '.join('%s: %s' % (k,v) for k,v in t))


class DefaultRecord(Record):
    """
    A Record with default values

        >>> class Foo(DefaultRecord): pass
        >>> foo = Foo(name='Sam')
        >>> foo.name
        'Sam'
        >>> foo.phone
        ''
    """

    def __getitem__(self, name):
        try:
            return Record.__getitem__(self, name)
        except KeyError:
            return ''


class RecordList(list):
    """a list of Records"""

    def __str__(self):
        """
        represent as a string 

            >>> import datetime
            >>> class Person(Record): pass
            >>> class People(RecordList): pass
            >>> people = People()
            >>> people.append(Person(_id=1, name='Joe', age=20, birthdate=datetime.date(1992,5,5)))
            >>> people.append(Person(_id=2, name='Samuel', age=25, birthdate=datetime.date(1992,4,5)))
            >>> people.append(Person(_id=3, name='Sam', age=35, birthdate=datetime.date(1992,3,5)))
            >>> print people
            person
                id  age  name    birthdate   
            ------- ---- ------- ----------- 
                 1  20   Joe     1992-05-05  
                 2  25   Samuel  1992-04-05  
                 3  35   Sam     1992-03-05  
            3 records

            >>> people = People()
            >>> people.append(Person(userid=1, name='Joe', age=20, birthdate=datetime.date(1992,5,5)))
            >>> people.append(Person(userid=2, name='Samuel', age=25, birthdate=datetime.date(1992,4,5)))
            >>> people.append(Person(userid=3, name='Sam', age=35, birthdate=datetime.date(1992,3,5)))
            >>> print people
            person
            userid  age  name    birthdate   
            ------- ---- ------- ----------- 
            1       20   Joe     1992-05-05  
            2       25   Samuel  1992-04-05  
            3       35   Sam     1992-03-05  
            3 records

        """
        if len(self)==0:
            return 'Empty list'
        title=['%s\n' % kind(self[0])]

        data_lengths = {}
        for rec in self:
            for field in self[0].keys():
                n = data_lengths.get(field, 0)
                m = len('%s' % rec.get(field, ''))
                if n < m:
                    data_lengths[field] = m

        fields = data_lengths.keys()
        d = data_lengths
        fields.sort(lambda a,b:not d[a] and -999 or not d[b] and -999 or d[a]-d[b])

        lines  = []
        fmtstr = []

        if '_id' in fields:
            fields.remove('_id')
            fields.insert(0, '_id')
            title.append('    id  ')
            lines.append('------- ')
            fmtstr.append('%6d  ')
            ofields = fields[1:]
        else:
            ofields = fields

        for field in ofields:
            width = max(len(field),d[field])+1
            fmt = '%-' + ('%ds ' % width)
            fmtstr.append(fmt)
            title.append(fmt % field)
            lines.append(('-' * width) + ' ')
        fmtstr.append('')
        lines.append('\n')
        title.append('\n')
        t = []
        fmtstr = ''.join(fmtstr)

        for rec in self:
            values = [rec.get(key) for key in fields]
            t.append(''.join(fmtstr) % tuple(values))
        return ''.join(title) + ''.join(lines) + '\n'.join(t) + ('\n%s records' % len(self))

    def __init__(self, *a, **k):
        list.__init__(self, *a, **k)
        self._n = 0

    def __iter__(self):
        self._n = 0
        return self

    def next(self):
        if self._n >= len(self):
            raise StopIteration
        else:
            result = self[self._n]
            self._n += 1
        return result


class ItemList(list):
    """
    list of data items

    >>> items = ItemList()
    >>> items.append(['Joe', 12, 125])
    >>> items
    [['Joe', 12, 125]]
    >>> print items
    Column 0  Column 1  Column 2  
    --------- --------- --------- 
    Joe       12        125      

    >>> items.insert(0, ['Name', 'Score', 'Points'])
    >>> print items
    Name  Score  Points  
    ----- ------ ------- 
    Joe   12     125    

    >>> data = [
    ...     ['Joe', 12, 125],
    ...     ['Sally', 13, 135],
    ... ]
    >>> items = ItemList(data)
    >>> print items
    Column 0  Column 1  Column 2  
    --------- --------- --------- 
    Joe       12        125      
    Sally     13        135      


    >>> data = [
    ...     ['Joe', 12, 125],
    ...     ['Sally', 13, 135],
    ... ]
    >>> items = ItemList(data, labels=['Name', 'Score', 'Points'])
    >>> print items
    Name   Score  Points  
    ------ ------ ------- 
    Joe    12     125    
    Sally  13     135    


    """
    def __init__(self, *args, **kwargs):
        self.labels = kwargs.pop('labels', None)
        list.__init__(self, *args, **kwargs)

    def __str__(self):
        def is_numeric(value):
            return type(value) in [int, float, Decimal]

        def is_text(value):
            return type(value) in [str, unicode]

        def name_column(number):
            return 'Column {}'.format(number)

        if len(self) == 0:
            return ''

        num_columns = len(self[0])

        # calculate labels
        if self.labels:
            labels = self.labels
            offset = 0
        else:
            # if first row is not all text it doesn't contain labels so generate them
            if not all(is_text(label) for label in self[0]):
                labels = [name_column(i) for i in range(num_columns)]
                offset = 0
            else:
                labels = self[0]
                offset = 1

        # calculate column lengths
        data_lengths = {}
        for rec in self[offset:]:
            for i, col in enumerate(rec):
                n = data_lengths.get(i, 0)
                m = len('%s' % rec[i])
                if n < m:
                    data_lengths[i] = m

        fields = data_lengths.keys()
        d = data_lengths
        fields.sort(lambda a, b: not d[a] and -999 or not d[b] and -999 or d[a] - d[b])

        title = []
        lines = []
        fmtstr = []

        for i, label in enumerate(labels):
            width = max(len(label), d[i]) + 1
            fmt = '%-' + ('%ds'% width)
            fmtstr.append(fmt)
            title.append(fmt % label)
            lines.append(('-' * width) + '')
        title.append('\n')
        lines.append('\n')
        fmtstr = ' '.join(fmtstr)

        t = []

        for rec in self[offset:]:
            t.append(fmtstr % tuple(rec))

        return ' '.join(title)  + ' '.join(lines) + '\n'.join(t)



class OrderedSet(collections.MutableSet):
    """
    A Record with default values

        >>> s = OrderedSet('abracadaba')
        >>> t = OrderedSet('simsalabim')
        >>> print(s | t)
        OrderedSet(['a', 'b', 'r', 'c', 'd', 's', 'i', 'm', 'l'])
        >>> print(s & t)
        OrderedSet(['a', 'b'])
        >>> print(s - t)
        OrderedSet(['r', 'c', 'd'])

    credit: http://code.activestate.com/recipes/576694/
    Licensed under MIT License
    """

    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]         # sentinel node for doubly linked list
        self.map = {}                   # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:
            key, prev, next = self.map.pop(key)
            prev[2] = next
            next[1] = prev

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)


def parents(path):
    if not os.path.isdir(path):
        return parents(os.path.split(os.path.abspath(path))[0])
    parent = os.path.abspath(os.path.join(path, os.pardir))
    if path == parent:
        return []
    else:
        return [path] + parents(parent)


def locate_config(filename='services.ini', start='.'):
    for path in parents(start):
        pathname = os.path.join(path, filename)
        if os.path.exists(pathname):
            return pathname
    for path in parents(os.path.join(os.path.expanduser('~'))):
        pathname = os.path.join(path, filename)
        if os.path.exists(pathname):
            return pathname


class Config(object):

    def __init__(self, filename):
        self.config = ConfigParser.ConfigParser()
        if not filename or not os.path.exists(filename):
            raise Exception('%s file missing' % filename)
        self.config.read(filename)

    def get(self, section, option, default=None):
        try:
            return self.config.get(section, option)
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            if default != None:
                return default
            raise


if __name__ == '__main__':
    import doctest
    doctest.testmod()
