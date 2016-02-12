class ConfiguratorError(Exception):
    pass
    # def __init__(self, message):
    #     super(ConfiguratorError, self).__init__(message)


class ConfiguratorUserError(ConfiguratorError):
    def __init__(self, message, details):
        super(ConfiguratorUserError, self).__init__(message)
        self.details = details

    def text(self):
        return str(self.message) + '\n\n' + str(self.details)
