"""generic events dispatcher


Copyright (c) 2017 Braiins Systems s.r.o.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""


class EventDispatcher(object):
    """Dispatches events about parts of the build.

    """
    def __init__(self):
        self.subscribers = []

    def subscribe(self, subscriber):
        self.subscribers.append(subscriber)

    def register_feature_object(self, *args, **kw):
        self.dispatch('register_feature_object', *args, **kw)

    def register_built_in_object(self, *args, **kw):
        self.dispatch('register_built_in_object', *args, **kw)

    def register_component_program(self, *args, **kw):
        self.dispatch('register_component_program', *args, **kw)

    def dispatch(self, method, *args, **kw):
        for s in self.subscribers:
            getattr(s, method)(*args, **kw)


dispatcher = EventDispatcher()
