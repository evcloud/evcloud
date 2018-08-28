from abc import ABCMeta, abstractmethod
import xml.dom.minidom
from .manager import ImageManager

class AbsXML(object, metaclass=ABCMeta):
    @abstractmethod
    def _get_xml_tpl(self):pass

    def render(self, argv):
        xml_tpl = self._get_xml_tpl()
        if not xml_tpl:
            raise Exception('xml not find.')
        return xml_tpl % argv

class XMLEditor(object):
    def set_xml(self, xml_string):
        try:
            self._dom = xml.dom.minidom.parseString(xml_string)
        except Exception as e:
            return False
        else:
            return True

    def get_dom(self):
        if self._dom:
            return self._dom
        return None

    def get_root(self):
        if self._dom:
            return self._dom.documentElement
        return None

    def get_node(self, path):
        node = self._dom.documentElement
        for tag in path:
            find = False
            for child_node in node.childNodes:
                if child_node.nodeName == tag:
                    find = True
                    node = child_node
                    break
            if not find:
                return None
        return node



class DomainXML(AbsXML, XMLEditor):
    def __init__(self, image_id):
        self._image_id = image_id

    def _get_xml_tpl(self):
        return ImageManager().get_xml_tpl(self._image_id)

