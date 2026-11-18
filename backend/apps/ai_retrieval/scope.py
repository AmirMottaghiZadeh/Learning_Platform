"""A question owns one root selection; follow-up retrieval never resets it."""
from dataclasses import dataclass, field


@dataclass
class SourceScope:
    roots: tuple = ()
    related: dict = field(default_factory=dict)
    established: bool = False
    initial_fallback: bool = False

    @property
    def ids(self):
        return (*self.roots, *self.related)

    def bind(self, identifiers, *, fallback=False):
        if self.established:
            raise ValueError("SOURCE_SCOPE_ALREADY_BOUND")
        self.roots = tuple(dict.fromkeys(str(i) for i in identifiers))
        self.initial_fallback = fallback
        self.established = True

    def follow(self, parent, target, *, limit, kind="source_link"):
        parent, target = str(parent), str(target)
        if parent not in self.ids:
            return False
        if target in self.ids:
            return True
        if len(self.related) >= limit:
            return False
        self.related[target] = {"parent": parent, "kind": kind}
        return True

    def audit(self):
        return {"roots": list(self.roots), "related": dict(self.related),
                "initial_fallback": self.initial_fallback, "global_followup_searches": 0}
