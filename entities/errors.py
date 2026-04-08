class NotFoundError(Exception):
    """データが見つからない場合の例外"""

    def __init__(self, message: str = "Resource not found"):
        self.message = message
        super().__init__(self.message)


class AlreadyTakenError(Exception):
    """すでに同じデータが存在する場合の例外"""

    def __init__(self, message: str = "Resource has already been taken"):
        self.message = message
        super().__init__(self.message)


class AuthenticationError(Exception):
    """認証での例外"""

    def __init__(self, message: str = "Authentication Error"):
        self.message = message
        super().__init__(self.message)


class ForbiddenError(Exception):
    """権限での例外"""

    def __init__(self, message: str = "Forbidden Error"):
        self.message = message
        super().__init__(self.message)


class APIError(Exception):
    """外部APIでの例外"""

    def __init__(self, message: str = "API Error"):
        self.message = message
        super().__init__(self.message)


class ValidationError(Exception):
    """バリデーションエラー (400 Bad Request)"""

    def __init__(self, message: str = "Validation error"):
        self.message = message
        super().__init__(self.message)
