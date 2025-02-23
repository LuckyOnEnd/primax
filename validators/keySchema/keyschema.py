from marshmallow import Schema, fields, validates, ValidationError
from enum import Enum

# Marshmallow schema
class keySchema(Schema):
    # Define fields with validation
    api_key = fields.String(
        required=True,
        validate=lambda x: len(x) > 0,
        error_messages={"required": "API key is required."},
    )
    api_sec = fields.String(
        required=True,
        validate=lambda x: len(x) > 0,
        error_messages={"required": "API secret is required."},
    )
    type = fields.String(required=True, error_messages={"required": "Type is invalid."})

    amount = fields.Float(
        required=True,
        error_messages={"required": "Amount is required.",
                        "invalid": "Amount must be a positive number greater than 500."},
    )

    trading_view_login = fields.String(
        required=True,
        validate=lambda x: len(x) > 0,
        error_messages={"required": "TradingView Id is required."},
    )

    trading_view_password = fields.String(
        required=True,
        validate=lambda x: len(x) > 0,
        error_messages={"required": "TradingView Password is required."},
    )

    trading_view_chart_link = fields.String(
        required=True,
        validate=lambda x: len(x) > 0,
        error_messages={"required": "Chart link is required."},
    )

    @validates('type')
    def validate_type(self, key):
        if key not in ['spot', 'future']:
            raise ValidationError('Type is invalid. Must be Spot or Futures.')

    @validates('api_key')
    def validate_api_key(self, key):
        if len(key) != 64:
            raise ValidationError("API key is invalid. It must be exactly 64 characters.")

    @validates('api_sec')
    def validate_api_sec(self, key):
        if len(key) != 64:
            raise ValidationError("API Secret is invalid. It must be exactly 64 characters.")

    @validates('amount')
    def validate_amount(self, value):
        if value = 500:
            raise ValidationError("Amount must be greater than 500.")

    @validates('trading_view_login')
    def validate_trading_view_login(self, value):
        if len(value) < 3:
            raise ValidationError("TradingView Id needs to contain at least 3 characters.")

    @validates('trading_view_password')
    def validate_trading_view_password(self, value):
        if len(value) < 3:
            raise ValidationError("TradingView Password needs to contain at least 3 characters.")

    @validates('trading_view_chart_link')
    def validate_trading_view_chart_link(self, value):
        if len(value) < 3:
            raise ValidationError("Chart link needs to contain at least 3 characters.")
