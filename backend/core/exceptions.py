class VolatriaException(Exception):
    """Base exception for all Volatria Platform errors."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code

class OrderBookException(VolatriaException):
    """Raised for limit order book matching engine issues."""
    def __init__(self, message: str):
        super().__init__(message, code="ORDERBOOK_ERROR")

class PricingException(VolatriaException):
    """Raised for numerical/analytical option pricer issues."""
    def __init__(self, message: str):
        super().__init__(message, code="PRICING_ERROR")

class DatabaseException(VolatriaException):
    """Raised for database CRUD and session failures."""
    def __init__(self, message: str):
        super().__init__(message, code="DATABASE_ERROR")

class SecurityException(VolatriaException):
    """Raised for authorization, authentication, and RBAC issues."""
    def __init__(self, message: str):
        super().__init__(message, code="SECURITY_ERROR")

class BacktestException(VolatriaException):
    """Raised for event-driven backtest configuration or run issues."""
    def __init__(self, message: str):
        super().__init__(message, code="BACKTEST_ERROR")
