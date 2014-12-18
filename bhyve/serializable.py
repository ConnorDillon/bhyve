import yaml


class Serializable:
    def to_dict(self):
        vars(self)

    def dump(self):
        return yaml.dump(self.to_dict(), default_flow_style=False)

    @classmethod
    def from_dict(cls, dct):
        return cls(**dct)

    @classmethod
    def load(cls, yaml_str):
        return cls.from_dict(yaml.load(yaml_str))


def load_from_key_value(cls, dct):
    k, v = list(dct.items())[0]
    return cls(k, v)
