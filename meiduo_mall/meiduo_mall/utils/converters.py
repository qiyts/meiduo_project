class UsernameConverter:
    # 用户名的正则表达式--校验规则
    # 5-20位字符 数字 字母 下划线_ 横杠-
    regex = '[a-zA-Z0-9_-]{5,20}'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


class MobileConverter:
    # 手机号的正则
    regex = '1[3-9]\d{9}'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value