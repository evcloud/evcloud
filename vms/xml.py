from xml.dom import minidom


class XMLEditor(object):
    """
    xml文本编辑器
    """

    def set_xml(self, xml_desc):
        """
        设置要处理的xml文本

        :return:
            True: 成功
            False: 输入的xml文本无效
        """
        try:
            self._dom = minidom.parseString(xml_desc)
        except Exception as e:
            return False
        else:
            return True

    def get_dom(self):
        """
        获取xml的文档对象模型dom
        :return:
            success: minidom.Document()
            failed: None
        """
        try:
            return self._dom
        except Exception:
            pass

        return None

    def get_root(self):
        """
        获取根node节点
        :return:
        """
        if self._dom:
            return self._dom.documentElement
        return None

    def get_node_list(self, tag_path: str):
        """
        获取指定节点

        :param tag_path:   格式如：tag_name/tag_name/tag_name
        :return:
            NodeList()  # success
            None        # not found
        """
        tag_path = tag_path.strip('/')
        tag_names = tag_path.split('/')
        if len(tag_names) <= 0:
            return None

        node_list = [self._dom, ]
        for tag in tag_names:
            p_node = node_list[0]
            node_list = p_node.getElementsByTagName(tag)
            if len(node_list) <= 0:     # 未找到节点
                return None

        return node_list

    def create_node(self, tag_name: str, atter_dict: dict):
        """
        创建一个节点及属性

        :param tag_name: 节点名称
        :param atter_dict: 属性字典
        """

        if not atter_dict:
            return None

        doc = minidom.Document()
        new_node = doc.createElement(tag_name)

        for attr, value in atter_dict.items():
            # attr_key = doc.createAttribute(attr)
            # attr_key.nodeValue = value
            # new_node.setAttributeNode(attr_key)
            new_node.setAttribute(attr, value)

        return new_node
