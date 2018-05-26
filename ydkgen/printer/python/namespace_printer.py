#  ----------------------------------------------------------------
# Copyright 2016 Cisco Systems
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------

""" capabilities_printer.py

Print capabilities for bundle package.
"""
from ydkgen.printer.file_printer import FilePrinter
from ydkgen.api_model import Class, Enum, Package, get_property_name
from ydkgen.common import get_absolute_path_prefix, get_module_name, get_segment_path_prefix

class NamespacePrinter(FilePrinter):
    def __init__(self, ctx, one_class_per_module):
        super(NamespacePrinter, self).__init__(ctx)
        self.bundle_name = ''
        self.packages = None
        self.one_class_per_module = one_class_per_module

    def print_output(self, packages, bundle_name):
        self.packages = packages = [p for p in packages if p.bundle_name == bundle_name]
        self._print_bundle_name(bundle_name)
        self._print_capabilities(packages)
        self._print_entity_lookup(packages)
        self._print_namespace_lookup(packages)
        self._print_identity_lookup(packages)
        self._print_enum_lookup(packages)

    def _get_imports(self, packages):
        imports = set()
        for p in packages:
            for e in p.owned_elements:
                if e.stmt.keyword in ('container', 'list'):
                    imports.add(e.get_py_mod_name())
        return imports

    def _print_bundle_name(self, bundle_name):
        self.ctx.writeln('BUNDLE_NAME = "{}"'.format(bundle_name))
        self.ctx.bline()

    def _print_capabilities(self, packages):
        self.ctx.writeln('CAPABILITIES = {')
        self.ctx.lvl_inc()
        for p in self.packages:
            revision = p.stmt.search_one('revision')
            revision = '' if revision is None else revision.arg
            name = p.stmt.arg
            self.ctx.writeln('"{}": "{}",'.format(name, revision))
        self.ctx.lvl_dec()
        self.ctx.writeln('}')
        self.ctx.bline()

    def _print_entity_lookup(self, packages):
        self.ctx.writeln('ENTITY_LOOKUP = {')
        self.ctx.lvl_inc()
        for p in packages:
            ns = p.stmt.search_one('namespace')
            for e in p.owned_elements:
                if all((hasattr(e, 'stmt'), e.stmt is not None,
                        e.stmt.keyword in ('container', 'list'))):
                    if self.one_class_per_module:
                        pkg_name = e.get_package().name
                        prop_name = get_property_name(e, e.iskeyword)
                        self.ctx.writeln('("{}", "{}"): "{}.{}.{}.{}",'
                                         .format(ns.arg, e.stmt.arg, pkg_name, prop_name, prop_name, e.name))
                        self.ctx.writeln('("{}", "{}"): "{}.{}.{}.{}",'
                                         .format(p.stmt.arg, e.stmt.arg, pkg_name, prop_name, prop_name, e.name))
                    else:
                        self.ctx.writeln('("{}", "{}"): "{}",'
                                         .format(ns.arg, e.stmt.arg, e.fqn()))
                        self.ctx.writeln('("{}", "{}"): "{}",'
                                         .format(p.stmt.arg, e.stmt.arg, e.fqn()))

        self.ctx.lvl_dec()
        self.ctx.writeln('}')
        self.ctx.bline()

    def _print_namespace_lookup(self, packages):
        self.ctx.writeln('NAMESPACE_LOOKUP = {')
        self.ctx.lvl_inc()
        for p in packages:
            ns = p.stmt.search_one('namespace')
            # submodule
            if ns is None:
                continue
            name = p.stmt.arg
            self.ctx.writeln('"{}": "{}",'.format(name, ns.arg))
        self.ctx.lvl_dec()
        self.ctx.writeln('}')
        self.ctx.bline()

    def _print_identity_lookup(self, packages):
        packages = sorted(packages, key=lambda p:p.name)

        self.ctx.writeln('IDENTITY_LOOKUP = {')
        self.ctx.lvl_inc()
        for package in packages:
            identities = [idx for idx in package.owned_elements if isinstance(
                idx, Class) and idx.is_identity()]
            identities = sorted(identities, key=lambda c: c.name)
            for identity_clazz in identities:
                self.ctx.writeln("'%s:%s':('%s', '%s')," % (get_module_name(identity_clazz.stmt), identity_clazz.stmt.arg,
                                                                 identity_clazz.get_py_mod_name(), identity_clazz.qn()))
        self.ctx.lvl_dec()
        self.ctx.writeln('}')
        self.ctx.bline()

    def _print_enum_lookup(self, packages):
        packages = sorted(packages, key=lambda p:p.name)

        self.ctx.writeln('ENUM_LOOKUP = {')
        self.ctx.lvl_inc()

        enum_leafs = []
        for package in packages:
            class_index = 0
            classes = [elem for elem in package.owned_elements if isinstance(elem, Class) and not elem.is_identity()]

            while class_index < len(classes):
                clazz = classes[class_index]
                properties = sorted(clazz.properties(), key=lambda p:p.name)
                for prop in properties:
                    if isinstance(prop.property_type, Enum):
                        data = (prop.owner, prop.name, prop.get_py_mod_name(), prop.property_type.name)
                        enum_leafs.append(data)
                    elif prop.property_type.name == 'union':
                        for typ in prop.property_type.types:
                            if typ.i_type_spec.name == 'enumeration':
                                if hasattr(typ, 'i_enum'):
                                    enum = typ.i_enum
                                else:
                                    enum = typ.i_typedef.i_enum
                                data = (prop.owner, prop.name, enum.get_py_mod_name(), enum.name)
                                enum_leafs.append(data)
                classes.extend([nested_class for nested_class in clazz.owned_elements if isinstance(nested_class, Class)])
                class_index += 1

        for clazz, leaf_name, module_name, enum_name in enum_leafs:
            segpath_prefix = get_segment_path_prefix(clazz)
            segment_path = '%s/%s' % (segpath_prefix, leaf_name)
            abspath_prefix = get_absolute_path_prefix(clazz)

            key = '%s%s' % (abspath_prefix, segment_path)
            value = "('%s', '%s')," % (module_name, enum_name)
            self.ctx.writeln("'%s':%s" % (key, value))

        self.ctx.lvl_dec()
        self.ctx.writeln('}')
        self.ctx.bline()
