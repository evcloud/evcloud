class Error(Exception):
    '''
    错误定义
    '''
    def __init__(self, code: int = 0, msg: str = '', err=None, err_code: str = 'error'):
        '''
        :param code: 错误码
        :param msg: 错误信息
        :param err: 错误对象
        '''
        self.code = code
        self.msg = msg
        self.err_code = err_code
        self.err = err

    def __str__(self):
        return self.detail()

    def detail(self):
        '''错误详情'''
        if self.msg:
            return self.msg

        if self.err:
            return str(self.err)

        return '未知的错误'

    def data(self, msg_key: str = 'code_text'):
        return {
            'code': self.code,
            'err_code': self.err_code,
            msg_key: self.detail()
        }
