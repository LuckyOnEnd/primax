from marshmallow import Schema, fields, validates, ValidationError
from enum import Enum

# Marshmallow schema
class keySchema(Schema):
    # Define fields with validation
    account = fields.String(
        required=True,
        error_messages={"required": "Account is required."},
    )
    password = fields.String(
        required=True,
        error_messages={"required": "Password is required."},
    )
    server = fields.String(required=True, error_messages={"required": "Server is invalid."})
    signal_type = fields.String()

    amount = fields.Float(
        required=True,
        error_messages={"required": "Amount is required.",
                        "invalid": "Amount must be a positive number greater than 500."},
    )

    trading_view_login = fields.String(
    )

    trading_view_password = fields.String(
    )

    trading_view_chart_link = fields.String(
    )

    @validates('account')
    def validate_api_key(self, key):
        if len(key) < 0:
            raise ValidationError("Account is required.")

    @validates('password')
    def validate_api_sec(self, key):
        if len(key) < 0:
            raise ValidationError("Password is invalid")

    @validates('amount')
    def validate_amount(self, value):
        if value < 5:#todo only for testing
            raise ValidationError("Amount must be greater than 5.")

