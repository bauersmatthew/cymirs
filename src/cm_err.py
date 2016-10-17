"""Define simple, custom exception to throw."""
class CMErr:
    """Base exception."""
    def __init__(self, msg, code, sector):
        self.msg = msg
        self.err = code + sector
        self.code = code
        self.sector = sector
    def __repr__(self):
        return 'CMErr({s.msg}, {s.code}, {s.sector})'.format(self)
    def __str__(self):
        return '{s.msg} ({s.err})'.format(self).capitalize()
    def __int__(self):
        return self.err
        
class CMELoad:
    """For the JF loading routine."""
    def __init__(self, msg, code):
        super(msg, code, 0)
