from django.test import TestCase
from logrecord.manager import LogManager


# Create your tests here.


class LogRecordTest(TestCase):

    def test_extract_string(self):

        teststr1 = '[user]xxx@cnic.cn;备注'

        teststr2 = '[vo]vo_name;[user]xxx@cnic.cn;备注'

        teststr3 = '[user]xxx@cnic.cn;[user]1111@cnic.cn;备注'

        str = LogManager().extract_string_remark(text=teststr1, start_marker='[user]', end_marker=';')
        print(f'{str}')
        self.assertEqual(str, 'xxx@cnic.cn')

        str = LogManager().extract_string_remark(text=teststr2, start_marker='[user]', end_marker=';')
        print(f'{str}')
        self.assertEqual(str, 'xxx@cnic.cn')

        str = LogManager().extract_string_remark(text=teststr3, start_marker='[user]', end_marker=';')
        print(f'{str}')
        self.assertEqual(str, 'xxx@cnic.cn')


        teststr1 = '/api/v3/center/?_who_action=[user]xxx@cnic.cn'
        teststr2 = '/api/v3/center/?_who_action=[vo]vo_name;[user]xxx@cnic.cn'


        str = LogManager().extract_string_url(text=teststr1, start_marker='[user]')
        print(f'{str}')
        self.assertEqual(str, 'xxx@cnic.cn')
        #
        str = LogManager().extract_string_url(text=teststr2, start_marker='[user]')
        print(f'{str}')
        self.assertEqual(str, 'xxx@cnic.cn')
