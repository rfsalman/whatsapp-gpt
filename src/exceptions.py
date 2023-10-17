class BaseException(Exception):
  detail: dict
  def __init__(self, **kwargs):
    self.detail = kwargs.get('detail')

class EmailAlreadyExistsError(BaseException):
  pass

class UserCreationError(BaseException):
  pass

class UserForbiddenAccessError(BaseException):
  pass

class NotFoundError(BaseException):
  pass

class InternalServerError(BaseException):
  pass

class UserVerificationRequestError(BaseException):
  pass

class UpdateUserError(BaseException):
  pass

class UpdateUserCriteriaError(BaseException):
  pass

class UserBioInitializationError(BaseException):
  pass

class UserAlreadyVerifiedError(BaseException):
  pass

class UserNotVerifiedError(BaseException):
  pass

class UserMinPictureError(BaseException):
  pass

class DeleteBioPictureError(BaseException):
  pass

class IncorrectPasswordError(BaseException):
  pass

class UpdatePasswordError(BaseException):
  pass

class IncorectCurrentEmailError(BaseException):
  pass

class UpdateEmailError(BaseException):
  pass

class WingmanNotFoundError(BaseException):
  pass

class UserSelectWingmanError(BaseException):
  pass

class MatchAlreadyRejectedError(BaseException):
  pass

class MatchAlreadyExistsError(BaseException):
  pass

class WeaviateQueryError(BaseException):
  pass

class UserPicturesLimitError(BaseException):
  pass

class PushNotificationTokenError(BaseException):
  pass

def format_validation_errors(e):
  errors = {}
  print(e, ' <<< e format_validation_errors')
  for error in e.errors():
    field = '.'.join(error['loc'])
    if field in errors:
      # errors[field].append(error['msg'])
      errors[error['loc'][1]] = [error['msg']]
    else:
      errors[error['loc'][1]] = [error['msg']]
  error_response = errors
  return error_response