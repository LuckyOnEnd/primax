from marshmallow import Schema, fields, validates, ValidationError


class AuthSchema(Schema):
    user_id = fields.String(
        required=True,
        validate=lambda x: len(x) > 0,
        error_messages={"required": "UserID is required"},
    )
    password = fields.String(
        required=True,
        validate=lambda x: len(x) > 1,
        error_messages={"required": "Password is required"},
    )

    @validates('user_id')
    def validate_user_id(self, user_id):
        if len(user_id) == 0:
            raise ValidationError("UserID cannot be empty.")

    @validates('password')
    def validate_password(self, password):
        if len(password) <= 1:
            raise ValidationError("Password must be longer than 1 character.")
