from rest_framework.pagination import LimitOffsetPagination


class MacIpLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 256
