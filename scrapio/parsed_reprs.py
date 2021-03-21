import typing

class DispatchRepr:
    def __repr__(self) -> str:
        _repr = f"""
        Dispatch(\n
            vals={self._vals},
            children={self._children}
        )
        """
        return _repr

class a_HrefRepr:
    def __repr__(self) -> str:
        _repr = f"""
        A_Href(
            href={self.tree.tree_attrs["href"]},
            content={self.struct}

        )
        """
        return _repr

class ImgRepr:
    def __repr__(self) -> str:
        _repr = f"""
        Img(
            src={self.tree.tree_attrs["src"]},
            content={self.struct}

        )
        """
        return _repr

class StructuredRecordRepr:
    def __repr__(self) -> str:
        _repr = """
        StructuredRecord(
            records = {},
            content = {}
        )
        """.format(",\n".join(map(repr, self.records)), self.struct)
        return _repr

class MatchedRunRepr:
    def __repr__(self) -> str:
        _repr = """
        MatchedRun(
            runs = {},
            
        )
        """.format(",\n".join(map(repr, self.run_objs)))
        return _repr

class PatternMatcherRepr:
    def __repr__(self) -> str:
        _repr = """
        PatternMatcher(
            runs = {},
            struct = {}
        )
        """.format(",\n".join(map(repr, self.runs)), self.struct)
        return _repr
    

