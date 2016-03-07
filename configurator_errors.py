class ConfiguratorError(Exception):
    def __init__(self, message, details=None):
        super(ConfiguratorError, self).__init__(message)
        self.details = details

    def text(self):
        return str(self.message) + '\n\n' + str(self.details)



class ConfiguratorUserError(ConfiguratorError):
    def __init__(self, message, details):
        super(ConfiguratorUserError, self).__init__(message, details)


class ConfiguratorInternalError(ConfiguratorError):
    def __init__(self, message, details):
        super(ConfiguratorInternalError, self).__init__(message, details)
