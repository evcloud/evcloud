from xml.dom import minidom

class XMLEditor(object):
    '''
    xml文本编辑器
    '''
    def set_xml(self, xml_desc):
        '''
        设置要处理的xml文本

        :return:
            True: 成功
            False: 输入的xml文本无效
        '''
        try:
            self._dom = minidom.parseString(xml_desc)
        except Exception as e:
            return False
        else:
            return True

    def get_dom(self):
        '''
        获取xml的文档对象模型dom
        :return:
            success: minidom.Document()
            failed: None
        '''
        if self._dom:
            return self._dom
        return None

    def get_root(self):
        '''
        获取根node节点
        :return:
        '''
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

