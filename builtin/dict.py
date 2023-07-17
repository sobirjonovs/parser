class dict(dict):
    def set(self, key, **kwargs):
        """

        :param key:
        :param kwargs:
        """
        self.update({
            key: kwargs
        })
