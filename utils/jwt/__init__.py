from rest_framework_simplejwt.authentication import JWTAuthentication, InvalidToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

class JWTokenTool(JWTAuthentication):
    def get_query_jwt_value(self, request):
        '''
        尝试从query参数中获取jwt字符串
        :return:
            str
            None
        '''
        jwt = request.GET.get('jwt')
        return jwt if jwt else None

    def verify_jwt(self, jwt:str):
        '''
        校验jwt是否有效

        :param jwt: jwt字符串
        :return:
            token: Token()
        :raises: InvalidToken
        '''
        try:
            return self.get_validated_token(raw_token=jwt)
        except InvalidToken as e:
            raise e

    def verify_jwt_return_user(self, jwt:str, raise_error:bool=False):
        '''
        校验jwt是否有效, 校验通过返回用户

        :param jwt: jwt字符串
        :return:
            user or None
        :raises: AuthenticationFailed, InvalidToken
        '''
        try:
            token = self.verify_jwt(jwt=jwt)
            return self.get_user(token)
        except AuthenticationFailed as e:
            if raise_error:
                raise e
            return None

    def obtain_one_jwt(self, user):
        '''
        获取一个JWT token字符串
        :param user: 用户对象
        :return:
            token: str
        '''
        refresh = RefreshToken.for_user(user=user)
        return str(refresh.access_token)

    def authenticate_query(self, request):
        '''
        从query参数中获取jwt进行身份认证

        :param request:
        :return:
            (user, jwt)
        :raises: AuthenticationFailed, InvalidToken
        '''
        jwt = self.get_query_jwt_value(request)
        if jwt is None:
            return None

        user = self.verify_jwt_return_user(jwt=jwt, raise_error=True)
        return (user, jwt)