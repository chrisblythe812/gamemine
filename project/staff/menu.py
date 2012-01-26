from logging import debug
import itertools

from project.members.models import Group
   

class MenuElement(object):
    def __init__(self, elements):
        self.elements = elements
        self.all_elements = [self]
        for e in elements:
            self.all_elements += e.all_elements
        
    def filter(self, group):
        if not self.is_accessable(group):
            return None
        return self._clone(filter(None, map(lambda x: x.filter(group), self.elements))) 

    def is_accessable(self, group):
        return False

    def __repr__(self):
        lines = map(lambda x: '\n'.join(map(lambda a: '  ' + a, unicode(x).split('\n'))), self.elements)
        return '\n'.join(itertools.chain([self._get_title()], lines))

    def _get_title(self):
        return ''
    
    def _clone(self, elements):
        return MenuElement(elements)


class Section(MenuElement):
    def __init__(self, title, elements):
        super(Section, self).__init__(elements)
        self.title = title

    def is_accessable(self, group):
        return True

    def filter(self, group):
        new_section = super(Section, self).filter(group)
        return new_section if new_section.elements else None

    def __repr__(self):
        if self.elements:
            lines = map(lambda x: '\n'.join(map(lambda a: '    ' + a, unicode(x).split('\n'))), self.elements)
            return '\n'.join(itertools.chain(['<li><strong>%s</strong>' % self.title], ['  <ul>'], lines, ['  </ul>'], ['</li>']))
        else:
            return '<li><strong>%s</strong></li>' % self.title
    
    def _clone(self, elements):
        return Section(self.title, elements)


class MenuItem(MenuElement):
    def __init__(self, title, path, permissions, elements, status=None):
        super(MenuItem, self).__init__(elements)
        self.title = title
        self.path = path
        self.permissions = permissions
        self.status = status
        if status: 
            if callable(status):
                self.get_status = status
            else:
                self.get_status = lambda: status
        else:
            self.get_status = lambda: '' 
        
    def is_accessable(self, group):
        return Group.All in self.permissions or group in self.permissions

    def __repr__(self):
        if self.elements:
            lines = map(lambda x: '\n'.join(map(lambda a: '    ' + a, unicode(x).split('\n'))), self.elements)
            return '\n'.join(itertools.chain(['<li><a href="%s">%s</a>' % (self.path, self.get_title())], ['  <ul>'], lines, ['  </ul>'], ['</li>']))
        else:
            return '<li><a href="%s">%s</a></li>' % (self.path, self.get_title())
        
    def get_title(self):
        s = self.get_status()
        s = ' (%s)' % s if s else ''
        return self.title + s

    def _clone(self, elements):
        return MenuItem(self.title, self.path, self.permissions, elements, status=self.status)


class MainMenu(MenuElement):
    def __init__(self, elements):
        super(MainMenu, self).__init__(elements)
        self.menu_items = filter(lambda x: isinstance(x, MenuItem), self.all_elements)

    def is_accessable(self, group):
        return True
    
    def is_item_accessible(self, group, path):
        for item in self.menu_items:
            if item.path == path:
                debug('%s: %s', path, Group.All in item.permissions)
                return Group.All in item.permissions or group in item.permissions
        return False

    def __repr__(self):
        lines = map(lambda x: '\n'.join(map(lambda a: '  ' + a, unicode(x).split('\n'))), self.elements)
        return '\n'.join(itertools.chain(['<ul class="level1">'], lines, ['</ul>']))

    def _clone(self, elements):
        return MainMenu(elements)


def main_menu(*sections):
    return MainMenu(sections)

def section(title, *elements):
    return Section(title, elements)

def menu(title, url, permissions, *elements, **kwargs):
    status = kwargs.pop('status', None)
    return MenuItem(title, url, permissions, elements, status=status)
